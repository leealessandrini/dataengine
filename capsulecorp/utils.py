""" Capsule Corp Utilities Module """
import io
import os
import datetime
import itertools
from concurrent.futures import ThreadPoolExecutor
import zipfile
from urllib.parse import urlparse
import logging
import yaml
import boto3
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(message)s")
logging.getLogger("py4j").setLevel(logging.ERROR)

# https://stackoverflow.com/questions/51272814
yaml.Dumper.ignore_aliases = lambda *args: True

# Setup s3 keys
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')


def get_date_range(date_0, date_1):
    """
        This method creates a list of dates from d0 to d1.

        Args:
            date_0 (datetime.date): start date
            date_1 (datetime.date): end date
        Returns:
            date range
    """
    return [
        date_0 + datetime.timedelta(days=i)
        for i in range((date_1 - date_0).days + 1)]


def parse_s3_url(s3_url):
    """
        This method will parse an s3 url.

        Args:
            s3_url (str): s3 url

        Returns:
            s3 bucket name and s3 key
    """
    # Parse proper output url
    parse_result = urlparse(s3_url)
    # Return bucket name and s3 key
    return parse_result.netloc, parse_result.path[1:]


def get_dict_permutations(raw_dict):
    """
        This method will take a raw dictionary and create all unique
        permutations of key value pairs.

        Source: https://codereview.stackexchange.com/questions/171173

        Args:
            raw_dict (dict): raw dictionary

        Returns:
            list of unique key value dict permutations
    """
    # Set default
    dict_permutations = [{}]
    # Check whether input is valid nonempty dictionary
    if (type(raw_dict) == dict) and (len(raw_dict) > 0):
        # Make sure all values are lists
        dict_of_lists = {}
        for key, value in raw_dict.items():
            if type(value) != list:
                dict_of_lists[key] = [value]
            else:
                dict_of_lists[key] = value
        # Create all unique permutations
        keys, values = zip(*dict_of_lists.items())
        dict_permutations = [
            dict(zip(keys, v)) for v in itertools.product(*values)]

    return dict_permutations



def read_file_from_s3(s3_key, bucket):
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


def read_df_from_s3(s3_key, bucket, **kwargs):
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


def _write_bytes_to_s3(bytes_object, bucket_name, s3_key):
    """
        This method will write a bytes object to s3 provided a prefix.

        Args:
            bytes_object (bytes): object that will be written
            bucket_name (str): s3 bucket name
            s3_key (str): location to save file to s3

        Returns:
            Success boolean
    """
    # Setup boto3 s3 client
    client = boto3.client(
        's3', aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY)
    # Write object to s3
    response = client.put_object(
        Body=bytes_object, Bucket=bucket_name, Key=s3_key)
    # Return success
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


def write_df_to_s3(df, s3_url, sep=",", header=True):
    """
        This method will save a DataFrame to S3 provided the filename.

        Args:
            df (pandas.DataFrame): DataFrame that will be written to s3
            s3_url (str): s3 url where data will be written
            separator (str): Separator character for the csv

        Returns:
            success boolean
    """
    return _write_bytes_to_s3(
        # Encode pandas DataFrame to bytes object
        df.to_csv(None, index=False, sep=sep, header=header).encode(),
        # Parse s3 URL for bucket name and s3 key
        *parse_s3_url(s3_url))


def write_dict_to_s3(dict_object, s3_url):
    """
        This method will convert a dict to bytes using YAML and write them to
        a specified s3 location.

        Args:
            dict_object (dict): python dictionary
            s3_url (str): s3 url where data will be written

        Returns:
            success boolean
    """
    return _write_bytes_to_s3(
        # Encode dictionary
        yaml.dump(dict_object).encode(),
        # Parse s3 URL for bucket name and s3 key
        *parse_s3_url(s3_url))


def write_zip_to_s3(file_dict, s3_url):
    """
        This method will zip a dictionary of byte objects and save the file
        on s3.

        Args:
            file_dict (dict): filenames and their corresponding bytes
            s3_url (str): s3 url where data will be written

        Returns:
            success boolean
    """
    # Write bytes in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer, "a", zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zip_file:
        for key, value in file_dict.items():
            zip_file.writestr(key, value)
    # Write bytes buffer to file
    success = _write_bytes_to_s3(zip_buffer.getvalue(), *parse_s3_url(s3_url))
    # Close buffer
    zip_buffer.close()

    return success


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


def check_s3_path(bucket_name, s3_path):
    """
        This method will check whether the provided s3 path is valid.

        Args:
            bucket_name (str): name of s3 bucket
            s3_path (str): path to s3 file

        Returns:
            boolean for whether the path exists
    """
    s3 = boto3.client(
        's3', aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY)
    # --- Setup key ---
    # Remove bucket from path to get prefix if applicable
    if bucket_name in s3_path:
        s3_prefix = s3_path.split(bucket_name)[1][1:]
    else:
        s3_prefix = s3_path
    # Get prefix to the left of the glob character
    if "*" in s3_prefix:
        s3_prefix = s3_prefix.split("*")[0]
    # Get list response
    resp = s3.list_objects(Bucket=bucket_name, Prefix=s3_prefix, MaxKeys=1)

    return "Contents" in resp


def get_responses(
        bucket, prefix, s3_access_key=S3_ACCESS_KEY,
        s3_secret_key=S3_SECRET_KEY):
    """
        This method will get the file information for a given directory on s3.

        Args:
            bucket (str): name of s3 bucket
            prefix (str): directory within s3 bucket

        Returns:
            list of json responses from S3
    """
    client = boto3.session.Session().client(
        "s3", aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key)
    continuation_token = None
    responses = []
    # List objects within the given directory until the response is truncated
    while True:
        list_kwargs = dict(
            Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        # Add continuation token if not None
        if continuation_token:
            list_kwargs['ContinuationToken'] = continuation_token
        response = client.list_objects_v2(**list_kwargs)
        # Add valid reponses and update continuation token
        if 'Contents' in response:
            responses += response['Contents']
        # Exit while loop if at the end of the objects
        if not response.get('IsTruncated'):
            break
        continuation_token = response.get('NextContinuationToken')

    return responses


def get_s3_prefix_size(prefix_list, bucket):
    """
        This method will get the size of a list of s3 prefixes.

        Args:
            prefix_list (list): list of s3 prefixes
            bucket (str): name of s3 bucket

        Returns:
            size (in Gb)
    """
    responses = []
    for prefix in prefix_list:
        responses += get_responses(bucket, prefix)

    return round(sum([i["Size"] for i in responses]) / np.power(10, 9), 2)


def copy_file(bucket, old_key, new_key):
    """
        This method will copy a file in s3 given a task definition.

        Args:
            bucket (str): s3 bucket name
            old_key (str): old s3 prefix
            new_key (str): new s3 prefix

        Returns:
            success boolean and exception message
    """
    success = True
    s3 = boto3.resource(
        's3', aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY)
    # Try to copy file
    try:
        s3.Object(bucket, new_key).copy_from(
            CopySource=f"{bucket}/" + old_key)
    # If the copy fails for any reason set success to False
    except Exception as e:
        success = False

    return success


def copy_s3_files(key_map, bucket, worker_count=8, max_retries=1):
    """
        This method will function as a threaded s3 copy a set of key value
        pairs of old s3 keys and new s3 keys.

        Args:
            key_map (dict): map of old to new s3 prefixes
            bucket (str): s3 bucket
            worker_count (int): number of workers to spin up for copying
            max_retries (int): maximum number of copy retries for failed tasks

        Returns:
            success boolean
    """
    success = True
    old_keys = list(key_map.keys())
    new_keys = list(key_map.values())
    # Create a thread pood to multiprocess tasks
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        # Run initial tasks
        results = list(executor.map(
            copy_file, [bucket] * len(old_keys), old_keys, new_keys))
        failed_tasks = [i for i in range(len(results)) if not results[i]]
        # Retry at most the number of max retries
        retries = 0
        while len(failed_tasks) > 0 and retries < max_retries:
            # Resubmit failed tasks
            futures = [i.result() for i in [
                executor.submit(copy_file, bucket, old_keys[i], new_keys[i])
                for i in failed_tasks]]
            # Get updated failed tasks
            failed_tasks = [
                i for i in range(len(futures)) if not futures[i]]
            # Iterate retries
            retries += 1
        # If there are still failed tasks log error and reset success
        copies_failed = len(failed_tasks)
        if copies_failed > 0:
            logging.error(
                f"WARNING: {copies_failed} copies failed.")
            success = False

    return success
