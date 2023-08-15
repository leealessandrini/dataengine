"""
This module contains utility functions for MySQL Databases.
"""
import psycopg2


def get_connection(schema_name, host, port, user, password):
    """
    This function will establish a database connection.
    """
    return psycopg2.connect(
        dbname=schema_name, host=host, port=port, user=user,
        password=password)
