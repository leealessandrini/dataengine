import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from dataengine.utilities import athena_utils

# Mock data to simulate a query result
mock_result_data = [
    {'Data': [{'VarCharValue': '1'}, {'VarCharValue': 'apple'}]},
    {'Data': [{'VarCharValue': '2'}, {'VarCharValue': 'banana'}]}
]

mock_column_info = [
    {'Name': 'id'},
    {'Name': 'fruit'}
]

# Function to mock get_query_results
def mock_get_query_results(*args, **kwargs):
    return {
        'ResultSet': {
            'Rows': mock_result_data,
            'ResultSetMetadata': {
                'ColumnInfo': mock_column_info
            }
        }
    }

# Function to mock get_query_execution
def mock_get_query_execution(*args, **kwargs):
    return {
        'QueryExecution': {
            'Status': {
                'State': 'SUCCEEDED'
            }
        }
    }

def test_run_athena_query_succeeded():
    with patch('boto3.client') as mock_boto_client:  # Replace 'your_module' with the actual module name
        mock_athena = MagicMock()
        mock_boto_client.return_value = mock_athena
        mock_athena.start_query_execution.return_value = {
            'QueryExecutionId': 'mock_id'}
        mock_athena.get_query_execution.side_effect = mock_get_query_execution
        mock_athena.get_query_results.side_effect = mock_get_query_results
        # Read data from mocked athena
        df, success = athena_utils.run_athena_query(
            'fake_access_key', 'fake_secret_key', 'SELECT * FROM table',
            'test_db', 'primary')
        # Assert equivalence
        assert success == True
        assert not df.empty
        assert list(df.columns) == ['id', 'fruit']
        assert df.shape == (2, 2)
