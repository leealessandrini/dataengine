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
    def validate_delta_type(self, database_type):
        valid_args = ["postgresql", "mysql"]
        if database_type not in valid_args:
            raise ValidationError(
                f"Invalid database_type '{database_type}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))

    @post_load
    def create_database(self, input_data, **kwargs):
        return Database(**input_data)


class Database(object):
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
        else:
            return postgresql_utils.get_connection(
                schema_name, self.host, self.port, self.user, self.password)
