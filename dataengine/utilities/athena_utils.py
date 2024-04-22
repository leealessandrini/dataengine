"""
AWS Athena Utility Methods
"""
import time
from typing import Tuple, Optional
import pandas as pd
import boto3
import numpy as np

QUERY_STATUSES = ['SUCCEEDED', 'FAILED', 'CANCELLED']

def run_athena_query(
        access_key: str, secret_key: str, query: str, database: str,
        workgroup: str,  region: Optional[str] = None, sleep_time: int = 1
    ) -> Tuple[pd.DataFrame, bool]:
    """
    Executes an Athena query and fetches the results into a Pandas DataFrame.

    Args:
        access_key (str): AWS access key ID.
        secret_key (str): AWS secret access key.
        query (str): The SQL query string to execute.
        database (str): The Athena database to query against.
        workgroup (str): The Athena workgroup to use.
        sleep_time (int, optional):
            Time in seconds to wait before checking query status again.
            Defaults to 1.

    Returns:
        Tuple[pd.DataFrame, bool]:
            A tuple containing the query result as a Pandas DataFrame and a
            boolean indicating query success.
    """
    success = False
    df = pd.DataFrame()
    # Establish connection with Athena
    athena_client = boto3.client(
        'athena', aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region)
    # Start query and get execution ID
    response = athena_client.start_query_execution(
        QueryString=query, QueryExecutionContext={'Database': database},
        WorkGroup=workgroup)
    query_execution_id = response['QueryExecutionId']
    # Check the status of the query
    while True:
        status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id)
        query_status = status['QueryExecution']['Status']['State']
        # Exit loop when provided appropriate status
        if query_status in QUERY_STATUSES:
            break
        # Wait before checking again
        time.sleep(sleep_time)
    # If the query is successful, parse the result into a Pandas DataFrame
    if query_status == 'SUCCEEDED':
        success = True
        # Paginator object to retrieve the results of the query using
        # pagination
        paginator = athena_client.get_paginator('get_query_results')
        result_iterator = paginator.paginate(
            QueryExecutionId=query_execution_id)
        # Iterate over the result pages and extract the rows of data from each
        # page.
        rows = []
        for result in result_iterator:
            for row in result['ResultSet']['Rows']:
                rows.append(row['Data'])
        if rows:
            column_info = result[
                'ResultSet']['ResultSetMetadata']['ColumnInfo']
            column_names = [col['Name'] for col in column_info]
            data = [
                [value.get('VarCharValue', np.nan) for value in row]
                for row in rows[1:]  # Skip header row
            ]
            df = pd.DataFrame(data, columns=column_names)
    else:
      print(f"Query failed with status '{query_status}': {query_execution_id}")

    return df, success
