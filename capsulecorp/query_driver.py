""" This module will contain any query related functionality """
import logging


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
        conn = driver.connect(**driver_args)
        cur = conn.cursor()
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
