import io
import os
import datetime
import boto3
import pandas as pd

# Setup s3 keys
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')


def get_date_range(d0, d1):
    """
        This method creates a list of dates from d0 to d1.
        Args:
            d0 (datetime.date): start date
            d1 (datetime.date): end date
        Returns:
            date range
    """
    return [
        d0 + datetime.timedelta(days=i) for i in range((d1 - d0).days + 1)]


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


def get_distinct_values(spark_df, column_header):
    """
        Get the list of distinct values within a DataFrame column.
        Args:
            spark_df (pyspark.sql.dataframe.DataFrame): data table
            column_header (str): header string for desired column
        Returns:
            list of distinct values from the column
    """
    distinct_values = spark_df.select(column_header).distinct().rdd.flatMap(
        lambda x: x).collect()

    return distinct_values
