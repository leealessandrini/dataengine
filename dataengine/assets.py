import os
import re
from typing import List, Optional, Dict
import logging
import yaml
from marshmallow import Schema, fields, validates, post_load, ValidationError
from .utilities import mysql_utils, postgresql_utils

ENVIRONMENT_VAR_REGEX = re.compile(r"\{\{(.+?)\}\}")


class AssetSchema(Schema):
    """
    Base Asset Schema.
    """
    asset_name = fields.Str(required=True)


class BaseDatasetSchema(AssetSchema):
    """
    Schema for BaseDataset class.
    """
    s3_prefix = fields.Str(required=True)
    file_format = fields.Str(load_default="csv")
    header = fields.Bool(load_default=True)
    schema = fields.Dict(
        keys=fields.Str(), values=fields.Str(), required=False)
    
    @validates("file_format")
    def validate_file_format(self, file_format):
        """
        Validate the input file format.
        """
        valid_args = ["csv", "parquet", "delta", "avro", "json"]
        if file_format not in valid_args:
            raise ValidationError(
                f"Invalid file_format '{file_format}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))
    
    @post_load
    def make_dataset(self, data, **kwargs):
        return BaseDataset(**data)


class BucketSchema(AssetSchema):
    """
    Schema for Bucket class.
    """
    bucket_name = fields.Str(required=True)
    access_key = fields.Str()
    secret_key = fields.Str()
    datasets = fields.List(fields.Nested(BaseDatasetSchema))
    
    @post_load
    def make_bucket(self, data, **kwargs):
        return Bucket(**data)
    
class Asset:
    """
    The Asset class will function as our parent class for all different types
    of assets.
    """
    def __init__(self, asset_name: str):
        self.asset_name = asset_name


# Forward declaration for type hinting
class Bucket(Asset):
    pass


class BaseDataset(Asset):
    """
    Base Dataset class.
    """
    def __init__(
            self,
            asset_name: str,
            s3_prefix: str,
            file_format: str = "csv",
            header: bool = True,
            schema: Optional[Dict[str, str]] = None
    ):
        super().__init__(asset_name)
        self.s3_prefix = s3_prefix
        self.file_format = file_format
        self.header = header
        self.schema = schema
        # Initially, the dataset is not in any bucket
        self.bucket: Optional[Bucket] = None

    def set_bucket(self, bucket: Bucket):
        self.bucket = bucket

    def get_bucket_name(self):
        return self.bucket.bucket_name if self.bucket else "Unassigned"


class Bucket(Asset):
    """
    S3 Bucket class.
    """
    def __init__(
            self,
            asset_name: str,
            bucket_name: str,
            access_key: Optional[str] = None,
            secret_key: Optional[str] = None
    ):
        super().__init__(asset_name)
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.datasets: List[BaseDataset] = []

    def add_dataset(self, dataset: BaseDataset):
        self.datasets.append(dataset)
        dataset.set_bucket(self)  # Set the parent bucket of the dataset

    def get_dataset(self, s3_prefix: str):
        for dataset in self.datasets:
            if dataset.s3_prefix == s3_prefix:
                return dataset
        return None


class DatabaseSchema(AssetSchema):
    """
    Schema for specifying database specs.
    """
    database_type = fields.String(required=True)
    host = fields.String(required=True)
    port = fields.Integer(required=True)
    user = fields.String(required=True)
    password = fields.String(required=True)

    @validates("database_type")
    def validate_database_type(self, database_type):
        """ This function will validate the database type """
        valid_args = ["postgresql", "mysql"]
        if database_type not in valid_args:
            raise ValidationError(
                f"Invalid database_type '{database_type}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))

    @post_load
    def create_database(self, input_data, **kwargs):
        return Database(**input_data)


class Database(Asset):
    """
    This class will provide an generic interface layer on top of our database.
    """
    def __init__(
                self,
                asset_name: str,
                database_type,
                host,
                port,
                user,
                password
        ):
        """
        Setup database interface arguments.
        """
        super().__init__(asset_name)
        self.database_type = database_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def get_connection(self, schema_name):
        """
        This wrapper function will get a database connection.
        """
        if self.database_type == "mysql":
            return mysql_utils.get_connection(
                schema_name, self.host, self.port, self.user, self.password)
        return postgresql_utils.get_connection(
            schema_name, self.host, self.port, self.user, self.password)

    def delete(
            self, schema_name, table_name, delete_all=False, days=None,
            column_header=None):
        """
        This method will delete and optimize a table provided inputs.

        Args:
            schema_name (str): name of database schema
            table_name (str): name of database table
            delete_all (bool): whether to delete all rows
            days (int): number of days out to delete
            column_header (str): header for day filter

        Returns:
            deletion success boolean
        """
        delete_success = False
        # Connect to database
        conn = self.get_connection(schema_name)
        # Construct delete query string
        delete_query = f"DELETE FROM {table_name}"
        if delete_all:
            delete_query += ";"
        elif ((days is not None) and (column_header is not None)):
            delete_query += (
                f" WHERE DATE({column_header}) <= "
                f"CURDATE() - INTERVAL {days} DAY;")
        else:
            logging.error(
                "Either provide delete_all True or both days and column_header")
            return delete_success
        # Add table optimization if load location is Aurora
        if self.database_type == "mysql":
            delete_query += f"\nOPTIMIZE TABLE {table_name};"
        try:
            with conn.cursor() as cur:
                cur.execute(delete_query)
            conn.commit()
            delete_success = True
            logging.info(
                f"Successfully deleted rows beyond {days} days from {table_name}")
        except Exception as e:
            logging.error(f"Failed table deletion: {e}")

        return delete_success

    def load_into(self, schema_name, table_name, s3_location, **kwargs):
        """
        This wrapper function will load data into the database from S3.
        """
        # Connect to database
        conn = self.get_connection(schema_name)
        # TODO: Add connection check here
        # Wrap load data method
        if self.database_type == "mysql":
            success = mysql_utils.load_from_s3(
                conn, table_name, s3_location, **{
                    key: value for key, value in kwargs.items()
                    if key in (
                        "separator", "header", "replace", "header_list")})
        else:
            success = postgresql_utils.load_from_s3(
                conn, table_name, s3_location, **{
                    key: value for key, value in kwargs.items()
                    if key in ("separator", "header", "file_format")})
        # Log either success or failure
        if success:
            logging.info(
                f"Successfully loaded into the {self.database_name} "
                f"table {schema_name}.{table_name}")
        else:
            logging.error(
                f"Failed loading into the {self.database_name} "
                f"table {schema_name}.{table_name}")
        # Close connection
        conn.close()

        return success


def load_assets(asset_config_path_list):
    """
    This function will load a provided set of assets given a list of
    filepaths.
    """
    # Initialize asset map
    asset_map = {"buckets": {}, "base_datasets": {}, "databases": {}}
    # Iterate over input asset configuration paths
    for path in asset_config_path_list:
        # Use a context manager for file I/O
        with open(path, "r") as f:
            asset_config = yaml.safe_load(f)
        # Iterate over each asset and load it accordingly
        for asset_name, parameters in asset_config.items():
            asset_type = parameters["asset_type"]
            # Determine whether config parameter is an environment variable
            # and if it is pull the value from the environment
            config = {"asset_name": asset_name}
            for key, value in parameters.items():
                if key == "asset_type":
                    continue
                match = ENVIRONMENT_VAR_REGEX.fullmatch(value)
                if match:
                    value = os.getenv(match.group(1))
                # If the input value is a port cast it to an integer
                if key == "port" and re.fullmatch(r"[0-9]+", value):
                    value = int(value)
                # Set the final config value
                config[key] = value
            # Load asset
            if asset_type == "database":
                asset_map["databases"][asset_name] = DatabaseSchema().load(config)
            elif asset_type == "bucket":
                asset_map["buckets"][asset_name] = BucketSchema().load(config)
            elif asset_type == "base_dataset":
                asset_map["base_datasets"][asset_name] = BaseDatasetSchema(
                    ).load(config)

    return asset_map