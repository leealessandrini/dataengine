"""
This module contains utility functions for MySQL Databases.
"""
import pymysql
from pymysql.constants import CLIENT


def get_connection(schema_name, host, port, user, password):
    """
    This function will establish a database connection.
    """
    return pymysql.connect(
        db=schema_name, host=host, port=port, user=user, passwd=password,
        client_flag=CLIENT.MULTI_STATEMENTS)
