import io
import os
import boto3
import pandas as pd

# Setup s3 keys
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')


def read_file_from_s3(s3_key, bucket='ccp-stbloglanding2'):
    """
        This method will read files from s3 using a boto3 client.
        Args:
            s3_key (str): s3 prefix to file
            bucket (str): s3 bucket name
        Returns:
            bytes object
    """
    client = boto3.client(
        's3', aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY)
    file = client.get_object(Bucket=bucket, Key=s3_key)

    return file['Body'].read()


def read_df_from_s3(s3_key, bucket='ccp-stbloglanding2', **kwargs):
    """
        This method will read in data from s3 into a pandas DataFrame.
        Args:
            s3_key (str): s3 prefix to file
            bucket (str): s3 bucket name
        Returns:
            bytes object
    """
    return pd.read_csv(
        io.StringIO(str(read_file_from_s3(s3_key, bucket), "utf-8")),
        # Pass additional keyword arguments to pandas read_csv method
        **kwargs)
