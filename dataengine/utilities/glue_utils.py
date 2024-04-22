"""
AWS Glue Utility Functions
"""
import boto3


def create_glue_table(
        database_name, table_name, s3_path, columns, partition_keys, 
        is_delta=False, aws_access_key_id=None, aws_secret_access_key=None,
        aws_region_name=None):
    """
    Creates a table in the AWS Glue Data Catalog.

    This function creates a new table in the specified AWS Glue Data Catalog
    database using the provided table definition, including the storage
    descriptor and partition keys.

    Args:
        database_name (str): The name of the AWS Glue Data Catalog database.
        table_name (str): The name of the table to create.
        s3_path (str): The S3 path where the table data is stored.
        columns (list of dict):
            A list of dictionaries defining the table columns, where each
            dictionary includes 'Name' and 'Type' keys
            (e.g., {'Name': 'year', 'Type': 'int'}).
        partition_keys (list of dict):
            A list of dictionaries defining the table partition keys, similar
            to the columns argument.
        is_delta (bool, optional):
            Set to True to specify the table as a Delta table;
            defaults to False (Parquet).
        aws_access_key_id (str, optional):
            The AWS access key ID, if using credentials other than the default
            configured in your environment.
        aws_secret_access_key (str, optional):
            The AWS secret access key, if using credentials other than the
            default configured in your environment.
        aws_region_name (str, optional):
            The AWS region name where the Glue Data Catalog database is
            located.

    Returns:
        bool: True if the table was created successfully, False otherwise.
    """
    # Setup session arguments if applicable
    session_args = {}
    if aws_access_key_id and aws_secret_access_key:
        session_args['aws_access_key_id'] = aws_access_key_id
        session_args['aws_secret_access_key'] = aws_secret_access_key
    if aws_region_name:
        session_args['region_name'] = aws_region_name
    # Instantiate glue client
    session = boto3.Session(**session_args)
    glue_client = session.client('glue')
    # Create the table definition
    table_input = {
        'Name': table_name,
        'StorageDescriptor': {
            'Columns': columns,
            'Location': s3_path,
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
                'Parameters': {'serialization.format': '1'}
            }
        },
        'PartitionKeys': partition_keys,
        'TableType': 'EXTERNAL_TABLE',
        'Parameters': {'classification': 'parquet'}
    }
    # Specify the table as a Delta table if is_delta is True
    if is_delta:
        table_input['Parameters']['table_type'] = 'DELTA'
    # Attempt to create the table provided input parameters and return success
    try:
        glue_client.create_table(
            DatabaseName=database_name, TableInput=table_input)
        print(f"Table '{table_name}' created successfully.")
        return True
    except glue_client.exceptions.AlreadyExistsException:
        print(f"Table '{table_name}' already exists.")
        return False
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def delete_glue_table(
        database_name, table_name, aws_access_key_id=None,
        aws_secret_access_key=None, aws_region_name=None):
    """
    Deletes a table from the AWS Glue Data Catalog.

    Args:
        database_name (str): The name of the Glue Data Catalog database containing the table.
        table_name (str): The name of the table to delete.
        aws_access_key_id (str, optional):
            AWS access key ID, if not using the default configured in the
            environment.
        aws_secret_access_key (str, optional):
            AWS secret access key, if not using the default configured in the
            environment.
        aws_region_name (str, optional):
            The AWS region where the Glue Data Catalog database is located, if
            not using the default configured in the environment.

    Returns:
        bool: True if the table was deleted successfully, False otherwise.
    """
    # Setup session arguments if applicable
    session_args = {}
    if aws_access_key_id and aws_secret_access_key:
        session_args['aws_access_key_id'] = aws_access_key_id
        session_args['aws_secret_access_key'] = aws_secret_access_key
    if aws_region_name:
        session_args['region_name'] = aws_region_name
    # Instantiate glue client
    session = boto3.Session(**session_args)
    glue_client = session.client('glue')
    # Attempt to delete the table from the Glue Catelog
    try:
        glue_client.delete_table(DatabaseName=database_name, Name=table_name)
        print(f"Table '{table_name}' was deleted successfully.")
        return True
    except glue_client.exceptions.EntityNotFoundException:
        print(f"Table '{table_name}' not found.")
        return False
    except Exception as e:
        print(f"An error occurred while trying to delete table '{table_name}': {str(e)}")
        return False


def start_glue_crawler(
        crawler_name, aws_access_key_id=None, aws_secret_access_key=None,
        aws_region_name=None):
    """
    Starts an existing AWS Glue crawler.

    Args:
        crawler_name (str): The name of the AWS Glue crawler to start.
        aws_access_key_id (str, optional):
            AWS access key ID, if not using the default configured in the
            environment.
        aws_secret_access_key (str, optional):
            AWS secret access key, if not using the default configured in the
            environment.
        aws_region_name (str, optional):
            The AWS region where the Glue crawler is located, if not using the
            default configured in the environment.

    Returns:
        bool: True if the crawler was started successfully, False otherwise.
    """
    # Setup session arguments if applicable
    session_args = {}
    if aws_access_key_id and aws_secret_access_key:
        session_args['aws_access_key_id'] = aws_access_key_id
        session_args['aws_secret_access_key'] = aws_secret_access_key
    if aws_region_name:
        session_args['region_name'] = aws_region_name
    # Instantiate glue client
    session = boto3.Session(**session_args)
    glue_client = session.client('glue')
    # Attempt to start the crawler
    try:
        glue_client.start_crawler(Name=crawler_name)
        print(f"Crawler '{crawler_name}' started successfully.")
        return True
    except Exception as e:
        print(f"Failed to start crawler '{crawler_name}': {str(e)}")
        return False
