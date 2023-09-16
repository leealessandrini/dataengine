import pytest
import boto3
from moto import mock_s3
import pandas as pd
from capsulecorp.utilities import s3_utils

# Setup global variables
ACCESS_KEY = "testing"
SECRET_KEY = "testing"
BUCKET_NAME = "my-bucket"


@pytest.fixture
def aws_credentials():
    """Mock AWS Credentials for moto."""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = ACCESS_KEY
    os.environ['AWS_SECRET_ACCESS_KEY'] = SECRET_KEY
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture
def s3_client(aws_credentials):
    with mock_s3():
        conn = boto3.client("s3", region_name="us-east-1")
        yield conn


def setup_s3_bucket(s3_client):
    s3_client.create_bucket(Bucket=BUCKET_NAME)
    s3_client.put_object(
        Bucket=BUCKET_NAME, Key='test_textfile', Body=b'test_content')
    s3_client.put_object(
        Bucket=BUCKET_NAME, Key='test_csv', Body="col1,col2\n1,2\n3,4")


def test_is_valid_s3_url():
    # Test valid S3 URL
    assert s3_utils.is_valid_s3_url("s3://my-bucket/my_prefix") == True
    # Test valid S3 URL pointing to bucket root
    assert s3_utils.is_valid_s3_url("s3://my-bucket/") == True
    # Test invalid scheme
    assert s3_utils.is_valid_s3_url("http://my-bucket/my_prefix") == False
    # Test missing netloc (bucket)
    assert s3_utils.is_valid_s3_url("s3:///my_prefix") == False
    # Test missing path
    # Could be True, depending on our requirements
    assert s3_utils.is_valid_s3_url("s3://my-bucket") == False
    # Test completely invalid URL
    assert s3_utils.is_valid_s3_url("not_a_valid_url") == False
    # Test empty string
    assert s3_utils.is_valid_s3_url("") == False


def test_parse_url():
    # Test with typical valid S3 URL
    s3_url = 's3://my-bucket/my_prefix'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix == 'my_prefix'
    assert bucket == 'my-bucket'
    # Test with valid S3 URL pointing to bucket root
    s3_url = 's3://my-bucket/'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix == ''
    assert bucket == 'my-bucket'
    # Test with invalid scheme
    s3_url = 'http://my-bucket/my_prefix'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix is None
    assert bucket is None
    # Test with missing netloc (bucket)
    s3_url = 's3:///my_prefix'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix is None
    assert bucket is None
    # Test with missing path
    s3_url = 's3://my-bucket'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix is None  # Or '' depending on your requirements
    assert bucket is None  # Or 'my-bucket' depending on your requirements
    # Test completely invalid URL
    s3_url = 'not_a_valid_url'
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix is None
    assert bucket is None
    # Test with empty string
    s3_url = ''
    prefix, bucket = s3_utils.parse_url(s3_url)
    assert prefix is None
    assert bucket is None


def test_read_file(s3_client):
    setup_s3_bucket(s3_client)
    s3_prefix = 'test_textfile'
    result = s3_utils.read_file(ACCESS_KEY, SECRET_KEY, s3_prefix, BUCKET_NAME)
    assert result == b'test_content'


def test_read_df(s3_client):
    setup_s3_bucket(s3_client)
    s3_prefix = 'test_csv'
    # Get the test csv from the mocked bucket as a pandas DataFrame
    df = s3_utils.read_df(ACCESS_KEY, SECRET_KEY, s3_prefix, BUCKET_NAME)
    # Verify that the DataFrame is as expected
    expected_df = pd.DataFrame({'col1': [1, 3], 'col2': [2, 4]})
    pd.testing.assert_frame_equal(df, expected_df)


def test_write_bytes(s3_client):
    setup_s3_bucket(s3_client)
    # Setup test data
    s3_prefix = 'test_write_bytes'
    bytes_object = b"test_data"
    # Run the function
    success = s3_utils.write_bytes(
        ACCESS_KEY, SECRET_KEY, s3_prefix, BUCKET_NAME, bytes_object)
    # Verify the function return
    assert success == True
    # Verify that the object was written to S3
    written_data = s3_utils.read_file(
        ACCESS_KEY, SECRET_KEY, s3_prefix, BUCKET_NAME)
    assert written_data == bytes_object


def test_write_pandas_df_csv(s3_client):
    setup_s3_bucket(s3_client)
    # Setup args
    prefix = "test_write_dataframe.csv"
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    # Write DataFrame to S3
    success = s3_utils.write_pandas_df(
        ACCESS_KEY, SECRET_KEY, f's3://{BUCKET_NAME}/{prefix}', df)
    assert success == True
    # Verify that the DataFrame was written to S3
    written_df = s3_utils.read_df(
        ACCESS_KEY, SECRET_KEY, prefix, BUCKET_NAME)
    pd.testing.assert_frame_equal(written_df, df)


def test_write_pandas_df_parquet(s3_client):
    setup_s3_bucket(s3_client)
    # Setup args
    prefix = "test_write_dataframe.parquet"
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    # Write DataFrame to S3
    success = s3_utils.write_pandas_df(
        ACCESS_KEY, SECRET_KEY, f's3://{BUCKET_NAME}/{prefix}', df,
        file_format="parquet")
    assert success == True
    # TODO: Add verification that the DataFrame was written to S3


def test_write_pandas_df_unsupported_format(s3_client):
    setup_s3_bucket(s3_client)
    # Setup args
    prefix = "test_write_dataframe.unsupported"
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    # Write DataFrame to S3
    success = s3_utils.write_pandas_df(
        ACCESS_KEY, SECRET_KEY, f's3://{BUCKET_NAME}/{prefix}',
        df, file_format="unsupported")
    assert success == False
