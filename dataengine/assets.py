import os
import re
from typing import List, Optional, Dict, Union, Any
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
    file_path_list = fields.List(fields.Str(), required=True)
    file_format = fields.Str(load_default="csv")
    bucket_asset_name = fields.Str()
    header = fields.Bool(load_default=True)
    schema = fields.Dict(keys=fields.Str(), values=fields.Str())
    
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
            file_path_list: list,
            file_format: str = "csv",
            bucket_asset_name: str = None,
            header: bool = True,
            schema: Optional[Dict[str, str]] = None
    ):
        super().__init__(asset_name)
        self.file_path_list = file_path_list
        self.file_format = file_format
        self.header = header
        self.schema = schema
        # Setup location
        self.bucket_asset_name = bucket_asset_name
        if self.bucket_asset_name:
            self.location = "s3"
        else:
            self.location = "local"
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
    
    def truncate(
            self, schema_name, table_name
    ):
        """
        Truncates the specified table in the given schema.

        Args:
            schema_name (str): The name of the schema where the table resides
            table_name (str): The name of the table to be truncated

        Returns:
            bool: True if the table was successfully truncated, False otherwise
        """
        truncate_success = False
        conn = self.get_connection(schema_name)
        try:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {table_name};")
            conn.commit()
            truncate_success = True
            logging.info(f"Successfully truncated {table_name}")
        except Exception as e:
            logging.error(f"Failed table truncation: {e}")
        
        return truncate_success

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
                f"Successfully loaded into the {self.asset_name} "
                f"table {schema_name}.{table_name}")
        else:
            logging.error(
                f"Failed loading into the {self.asset_name} "
                f"table {schema_name}.{table_name}")
        # Close connection
        conn.close()

        return success


def load_asset_config_files(
        asset_config_path_list: List[str]
    ) -> Dict[str, Union[str, int, float, bool, list, dict]]:
    """
    Load asset configuration files from a list of file paths and merge them
    into a single dictionary.
    
    Args:
        asset_config_path_list (List[str]):
            A list of file paths to asset configuration files in YAML format.
    
    Returns:
        Dict[str, Union[str, int, float, bool, list, dict]]:
            A dictionary containing the merged asset configurations.
        
    Example:
        >>> load_asset_config_files(
        >>>    ["path/to/config1.yaml", "path/to/config2.yaml"])
        {'key1': 'value1', 'key2': 'value2'}
    """
    asset_config = {}
    # Iterate over input asset configuration paths
    for path in asset_config_path_list:
        # Use a context manager for file I/O
        with open(path, "r") as f:
            asset_config.update(yaml.safe_load(f))
    
    return asset_config


def load_assets(
        asset_config: Dict[str, Dict[str, Union[str, int, float, bool]]]
    ) -> Dict[str, Dict[str, Any]]:
    """
    Load assets from a configuration dictionary and organize them into
    different types.

    Args:
        asset_config (Dict[str, Dict[str, Union[str, int, float, bool]]]):
            A dictionary containing asset names as keys and another dictionary
            as values. The inner dictionary contains asset parameters including
            the asset type ('database', 'bucket', 'base_dataset') and other
            configurations.

    Returns:
        Dict[str, Dict[str, Any]]:
            A dictionary containing loaded assets organized into 'buckets',
            'base_datasets', and 'databases'.
    """
    # Initialize asset map
    asset_map = {"buckets": {}, "base_datasets": {}, "databases": {}}
    # Iterate over each asset and load it accordingly
    for asset_name, parameters in asset_config.items():
        # Assume asset is base dataset
        # TODO: Replace this when base datasets are updated
        if "asset_type" not in parameters:
            asset_type = "base_dataset"
        else:
            asset_type = parameters["asset_type"]
        # Determine whether config parameter is an environment variable
        # and if it is pull the value from the environment
        config = {"asset_name": asset_name}
        for key, value in parameters.items():
            if key == "asset_type":
                continue
            match = ENVIRONMENT_VAR_REGEX.fullmatch(str(value))
            if match:
                value = os.getenv(match.group(1))
            # If the input value is a port cast it to an integer
            if key == "port":
                if re.fullmatch(r"[0-9]+", str(value)):
                    value = int(value)
                else:
                    value = 0
            # If the value is still None cast it to an empty string
            if value is None:
                value = ""
            # Set the final config value
            config[key] = value
        # Load asset
        if asset_type == "database":
            asset_map["databases"][asset_name] = DatabaseSchema().load(config)
        elif asset_type == "bucket":
            asset_map["buckets"][asset_name] = BucketSchema().load(config)
        elif asset_type == "base_dataset":
            asset_map["base_datasets"][asset_name] = BaseDatasetSchema().load(
                config)
    # Setup linkage between buckets and datasets
    # TODO: Setup bucket / base_dataset linkage here

    return asset_map
