"""
This module contains utility functions for MySQL Databases.
"""
import pymysql
from pymysql.constants import CLIENT


def get_connection(database_name, host, port, user, password):
    """
    This function will establish a database connection.
    """
    return pymysql.connect(
        db=database_name, host=host, port=port, user=user, passwd=password,
        client_flag=CLIENT.MULTI_STATEMENTS)
