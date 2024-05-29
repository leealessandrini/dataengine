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
