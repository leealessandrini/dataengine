""" This module will contain any query related functionality """
import os
import logging
import pymysql
from pymysql.constants import CLIENT
import psycopg2
import pandas as pd

# Setup s3 keys
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')


def connect_to_db(driver, driver_args):
    """
        This method will establish a connection to the Redshift database.

        Args:
            driver (): database driver module
            driver_args (dict): map of database connection args

        Returns:
            db connnection, connection cursor, and success bool
    """
    connection_success = True
    try:
        if driver.__name__ in ('pymysql', 'psycopg2'):
            conn = driver.connect(**driver_args)
            cur = conn.cursor()
        elif driver.__name__ == "sqlalchemy":
            # Create the engine object
            engine = driver.create_engine(
                "mysql+pymysql://{}:{}@{}:{}/{}".format(
                    driver_args['user'], driver_args['password'],
                    driver_args['host'], driver_args['port'],
                    driver_args['database']))
            # Create a connection
            conn = engine.connect()
            cur = None
        else:
            logging.error("Invalid driver provided.")
            raise Exception
        logging.info("Database connection successful.")
    except Exception:
        conn = None
        cur = None
        connection_success = False
        logging.error("Database connection failure.", exc_info=True)

    return conn, cur, connection_success


def execute_query(conn, cur, query, message=None):
    """
        This method will safely execute the given query and log the result.

        Args:
            conn (psycopg2.extensions.connection): db connection
            cur (psycopg2.extensions.cursor): connection cursor
            query (str): sql query string
            message (str): logging message corresponging to query

        Returns:
            query success boolean
    """
    # Try to execute query given cursor and connection
    success = True
    try:
        cur.execute(query)
        conn.commit()
        if message:
            logging.info(message + " success.")
    # Catch exception and log error
    except Exception:
        success = False
        if message:
            logging.error(message + " failed.", exc_info=True)

    return success


def delete(
        conn, cur, table_name, load_location, delete_all=False, days=None,
        column_header=None):
    """
        This method will delete and optimize a table provided inputs.

        Args:
            conn (pymysql.connections.Connection): database connection
            table_name (str): name of database table
            load_location (str): database type
            delete_all (bool): whether to delete all rows
            days (int): number of days out to delete
            column_header (str): header for day filter

        Returns:
            deletion success boolean
    """
    delete_success = False
    # Construct delete query string
    delete_query = f"DELETE FROM {table_name}"
    if delete_all:
        delete_query += ";"
        msg = f"Deletion of all rows from {table_name}."
    elif ((days is not None) and (column_header is not None)):
        delete_query += (
            f" WHERE DATE({column_header}) <= "
            f"CURDATE() - INTERVAL {days} DAY;")
        msg = f"Deletion of rows beyond {days} days from {table_name}."
    else:
        logging.error(
            "Either provide delete_all True or both days and column_header")
        return delete_success
    # TODO: Change this to a keyword arg and remove load location
    # Add table optimization if load location is Aurora
    if "aurora" in load_location.lower():
        delete_query += f"\nOPTIMIZE TABLE {table_name};"

    return execute_query(conn, cur, delete_query, msg)


def copy_from_s3(
        load_location, driver_args, table_name, s3_location,
        file_format="csv", separator=",", header=True, delete_info={},
        replace=False, header_list=[]):
    """
        This method will allow you to copy data of different formats from s3
        to a database or data warehouse like AWS Aurora or AWS Redshift.

        Args:
            load_location (str): database type
            driver_args (string): database connection arguments
            table_name (string): database table name
            s3_location (string): prefix of dataset on s3
            separator (string): csv separator
            header_list (list): list of table headers in-order

        Returns:
            success boolean
    """
    load_success = False
    # Setup query
    if "aurora" in load_location.lower():
        driver = pymysql
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
            {replace_rows}INTO TABLE `{table_name}`
            FIELDS TERMINATED BY '{separator}'{ignore_rows}{header_info};
        """
    elif "redshift" in load_location.lower():
        driver = psycopg2
        # Setup conversion parameters for csv
        # TODO: implement header_info argument into redshift query format
        ignore_header = " IGNOREHEADER 1 " if header else " "
        conversion_params = (
            f"DELIMITER '{separator}'{ignore_header}MAXERROR AS 10000;")
        if file_format == "parquet":
            conversion_params = "FORMAT AS PARQUET;"
        # Fill parameters
        query = f"""
            COPY {table_name}
            FROM '{s3_location}'
            ACCESS_KEY_ID '{S3_ACCESS_KEY}'
            SECRET_ACCESS_KEY '{S3_SECRET_KEY}'
            {conversion_params}
        """
    # Establish database connection
    conn, cur, success = connect_to_db(driver, driver_args)
    # If connection is valid, load data
    if success:
        # Execute delete query if applicable
        delete_success = True
        if delete_info:
            delete_success = delete(
                conn, cur, table_name, load_location, **delete_info)
        # Copy data from s3 to Database / Data Warehouse
        load_success = execute_query(
            conn, cur, query, f"Loading of {s3_location} into {table_name}")
        # Close connection
        conn.close()

    return load_success


def collect_query_result(conn, query, message):
    """
        This method will safely collect the result of a query and return it as
        a pandas DataFrame.

        Args:
            conn (psycopg2.extensions.connection): db connection
            query (str): sql query string
            message (str): logging message corresponging to query

        Returns:
            query result and success boolean
    """
    success = True
    try:
        result = pd.read_sql(query, con=conn)
        logging.info(message + " success.")
    except Exception:
        success = False
        result = pd.DataFrame()
        logging.error(message + " failed.", exc_info=True)

    return result, success


def check_table_existence(conn, table_name):
    """
        This method will check the database schema for the provided table.

        Args:
            conn (pymysql.connections.Connection): database connection
            table_name (str): database table name

        Returns:
            existence boolean
    """
    table_exists = False
    # Check whether date table exists
    stmt = f"SHOW TABLES LIKE '{table_name}'"
    cur = conn.cursor()
    cur.execute(stmt)
    result = cur.fetchone()
    if result:
        table_exists = True
    cur.close()

    return table_exists
