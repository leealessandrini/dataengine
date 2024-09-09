import os
from typing import List, Optional, Dict, Union
import logging
from marshmallow import Schema, fields, validates, post_load, ValidationError
from .utilities import mysql_utils, postgresql_utils, general_utils


class AssetSchema(Schema):
    """
    Base Asset Schema.
    """
    asset_name = fields.Str(required=True)
    dirname = fields.Str(required=True)
    description = fields.Str()


class BaseDatasetSchema(AssetSchema):
    """
    Schema for BaseDataset class.
    """
    file_path = general_utils.StringOrListField(required=True)
    file_format = fields.Str(load_default="csv")
    separator = fields.String(load_default=",")
    location = fields.Str(load_default="local")
    bucket_asset_name = fields.Str()
    header = fields.Bool(load_default=True)
    schema = fields.Dict()
    options = fields.Dict()
    
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

    @validates("schema")
    def validate_schema(self, schema):
        """
        Validate the 'schema' field to ensure it's a dictionary of key-value
        pairs where both keys and values are strings.
        """
        if not isinstance(schema, dict):
            raise ValidationError("Schema must be a dictionary.")

        for key, value in schema.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError(
                    "Schema keys and values must be strings.")
    
    @post_load
    def make_base_dataset(self, data, **kwargs):
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
    def __init__(self, asset_name: str, dirname: str, description: str = None):
        self.asset_name = asset_name
        self.dirname = dirname
        self.description = description


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
            dirname: str,
            file_path: Union[str, List[str]],
            file_format: str = "csv",
            separator: str = ",",
            location: str = "local",
            bucket_asset_name: str = None,
            header: bool = True,
            schema: Optional[Dict[str, str]] = None,
            options: Optional[Dict[str, str]] = {},
            **kwargs
    ):
        # Setup generic asset variables
        super().__init__(asset_name, dirname, description=kwargs.get("description"))
        # Setup filepath
        if isinstance(file_path, str):
            file_path = [file_path]
        self.file_path_list = file_path
        # Set base dataset parameters
        self.separator = separator
        self.file_format = file_format
        self.header = header
        self.schema = schema
        self.options = options
        # Override location to s3 if bucket name is provided
        self.bucket_asset_name = bucket_asset_name
        if self.bucket_asset_name:
            self.location = "s3"
        else:
            self.location = location
        # Get the relative normal path of for the local files
        if self.location == "local":
            self.file_path_list = [
                os.path.normpath(os.path.join(dirname, i))
                for i in self.file_path_list]
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
                dirname: str,
                database_type,
                host,
                port,
                user,
                password
        ):
        """
        Setup database interface arguments.
        """
        super().__init__(asset_name, dirname)
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

    def drop_table(self, schema_name: str, table_name: str):
        """
        This method will allow users to drop tables from a database provided
        schema and table names.

        Args:
            schema_name (str): name of database schema
            table_name (str): name of database table            

        Returns:
            success boolean
        """
        # Connect to database
        conn = self.get_connection(schema_name)
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {table_name};")
            conn.commit()
            logging.info(f"Successfully dropped {schema_name}.{table_name}")
            conn.close()
        except Exception as e:
            logging.error(f"Failed to drop table: {e}")
            return False

        return True

    def check_table_existence(
            self, database_name: str, table_name: str,
            schema_name: str = 'public'):
        """
        This method will check whether a table exists in a provided schema.

        Args:
            database_name (str): name of the database
            table_name (str): name of the table
            schema_name (str, optional): name of the schema

        Returns:
            boolean for whether the table exists
        """
        conn = self.get_connection(database_name)
        exists = False
        try:
            with conn.cursor() as cur:
                if self.database_type == "mysql":
                    # MySQL query
                    query = f"SHOW TABLES LIKE '{table_name}'"
                    cur.execute(query)
                    result = cur.fetchone()
                    exists = result is not None
                else:
                    # PostgreSQL / Redshift query
                    query = f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema_name}' AND
                        table_name = '{table_name}'
                    );
                    """
                    cur.execute(query)
                    result = cur.fetchone()
                    exists = result[0]
        except Exception as e:
            print(f"Error checking table existence: {e}")
        finally:
            conn.close()

        return exists
