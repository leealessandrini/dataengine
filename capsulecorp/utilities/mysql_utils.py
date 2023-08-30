"""
This module contains utility functions for MySQL Databases.
"""
import pymysql
from pymysql.constants import CLIENT


def get_connection(schema_name, host, port, user, password):
    """
    This function will establish a database connection.

    TODO: Add error handling
    """
    return pymysql.connect(
        db=schema_name, host=host, port=port, user=user, passwd=password,
        client_flag=CLIENT.MULTI_STATEMENTS)


def load_from_s3(
        conn, table_name, s3_location, separator=",", header=True,
        replace=False, header_list=None):
    """
    Load data from AWS S3 into a MySQL database.

    Args:
        conn (pymysql.connections.Connection): database connection
        table_name (string): database table name
        s3_location (string): prefix of dataset on s3
        separator (string): csv separator
        header_list (list): list of table headers in-order

    Returns:
        success boolean
    """
    # Set ignore row string given header boolean
    ignore_rows = "\n    IGNORE 1 ROWS" if header else ""
    replace_rows = "REPLACE " if replace else ""
    # Setup list of headers if applicable
    header_info = ""
    if header_list:
        header_info = " " + str(tuple(f"`{i}`" for i in header_list))
    # Fill parameters
    query = f"""
        LOAD DATA FROM S3 PREFIX '{s3_location}'
        {replace_rows}INTO TABLE {table_name}
        FIELDS TERMINATED BY '{separator}'{ignore_rows}{header_info};
    """
    # Execute query
    try:
        with conn.cursor() as cur:
            cur.execute(query)
        conn.commit()
        return True
    except Exception as e:
        # TODO: Improve logging here by standardizing query execution.
        print(e)
        return False
