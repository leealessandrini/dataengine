"""
This class will function as a general purpose DataBase API.
"""
import logging
from marshmallow import Schema, fields, post_load, validates, ValidationError
from .utilities import mysql_utils, postgresql_utils


class DatabaseSchema(Schema):
    """
    Schema for specifying database specs.
    """
    database_name = fields.String(required=True)
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


class Database:
    """
    This class will provide an generic interface layer on top of our database.
    """

    def __init__(
            self, database_name, database_type, host, port, user, password):
        """
        Setup database interface arguments.
        """
        self.database_name = database_name
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
