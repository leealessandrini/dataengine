import os
import logging
import datetime
from marshmallow import Schema, fields, post_load, validates, ValidationError
import pandas as pd
from .utilities import s3_utils, spark_utils, general_utils

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")


class TimeDeltaSchema(Schema):
    """
    Schema for specifying the time delta.
    """
    days = fields.Integer()
    hours = fields.Integer()
    weeks = fields.Integer()


class DtDeltaSchema(TimeDeltaSchema):
    """
    Schema for specifying the dt rolling or latest time delta.
    """
    delta_type = fields.String()

    @validates("delta_type")
    def validate_delta_type(self, delta_type):
        valid_args = ["latest", "rolling"]
        if delta_type not in valid_args:
            raise ValidationError(
                f"Invalid delta_type '{delta_type}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))


class TimestampConversionSchema(Schema):
    """
    Schema for specifying timestamp conversion parameters.
    """
    column_header = fields.String(required=True)
    # Will default to UTC if not provided
    timezone = fields.String()
    # Will default to column_header
    new_column_header = fields.String()


class DatasetSchema(Schema):
    """
        Dataset marshmallow validation schema.
    """
    spark = fields.Raw(required=True)
    dt = fields.DateTime(required=True)
    hour = fields.String(required=True)
    file_path = general_utils.StringOrListField(required=True)
    bucket = fields.String(required=True)
    format_args = fields.Dict()
    file_format = fields.String()
    column_headers = fields.List(fields.String())
    column_types = fields.List(fields.String())
    separator = fields.String()
    header = fields.Boolean()
    time_delta = fields.Nested(TimeDeltaSchema)
    timestamp_conversion = fields.List(
        fields.Nested(TimestampConversionSchema))
    dt_delta = fields.Nested(DtDeltaSchema)
    exclude_hours = fields.List(fields.String())
    rename = fields.Dict()
    location = fields.String(default="s3")

    @validates("file_format")
    def validate_file_format(self, file_format):
        valid_args = ["csv", "parquet", "delta", "avro", "json"]
        if file_format not in valid_args:
            raise ValidationError(
                f"Invalid file_format '{file_format}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))

    @validates("location")
    def validate_location(self, location):
        valid_args = ["s3", "local"]
        if location not in valid_args:
            raise ValidationError(
                f"Invalid location '{location}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))

    @post_load
    def create_dataset(self, input_data, **kwargs):
        return Dataset(**input_data)


class Dataset(object):
    """
    Dataset class.
    """

    def __init__(
            self, spark, dt, hour, file_path, bucket,
            format_args={}, file_format="csv", column_headers=[],
            column_types=[], separator=",", header=False,
            time_delta={"days": 0, "hours": 0, "weeks": 0},
            timestamp_conversion=[], dt_delta={}, exclude_hours=[],
            rename={}, location="s3", **kwargs
        ):
        """
        Dataset constructor.
        """
        self.spark = spark
        self.file_format = file_format
        # Get all unique permutations of the format arguments
        format_args_permutations = general_utils.get_dict_permutations(
            format_args)
        # Convert file path to list if a string was passed in
        if isinstance(file_path, str):
            file_path = [file_path]
        # Load data from s3 if that is what the location is set to
        if location == "s3":
            self.file_path_list = self._setup_s3_path(
                file_path, dt, hour, time_delta, bucket, 
                format_args_permutations, dt_delta, exclude_hours)
            # Load data into a pyspark DataFrame
            self.df = self._load_data_from_s3(
                column_headers, column_types, file_format, separator, header,
                rename=rename)
            # Convert timestamp if applicable
            if timestamp_conversion:
                for params in timestamp_conversion:
                    self.df = spark_utils.convert_timestamp(self.df, **params)
        # Otherwise assume the data is a local csv file
        else:
            self.file_path_list = file_path
            self.df = spark_utils.pandas_to_spark(spark, pd.concat([
                pd.read_csv(path) for path in file_path], ignore_index=True))

    def _setup_s3_path(
            self, s3_path, dt, hour, time_delta, bucket, format_args,
            dt_delta, exclude_hours):
        """
        This method will setup the s3 path for the dataset.

        Args:
            s3_path (str): input s3 path
            dt (datetime.datetime): datetime object
            hour (int|str): input hour
            bucket (str): bucket name
            format_args (list): list of unique format argument dicts
            dt_delta (dict): either rolling or latest day / hour range

        Returns:
            final dataset s3 path
        """
        dataset_s3_path_list = []
        # Apply time delta and modify dt and hour
        dt, hour = general_utils.apply_time_delta(dt, hour, time_delta)
        # Iterate over each path and format accordingly
        for path in s3_path:
            # Iterate over each unique set of format arguments
            for unique_format_args in format_args:
                if (
                    not dt_delta or
                    (dt_delta and dt_delta["delta_type"] == "rolling")
                ):
                    # Default input days to 0
                    input_days = 0
                    input_weeks = 0
                    # Setup input hour based on hour variable
                    if hour == "*":
                        input_hours = hour
                    else:
                        input_hours = 1
                    # Override values depending on dt_delta
                    if dt_delta and (dt_delta["delta_type"] == "rolling"):
                        if "days" in dt_delta:
                            input_days = dt_delta["days"]
                        if "hours" in dt_delta:
                            input_hours = dt_delta["hours"]
                        if "weeks" in dt_delta:
                            input_weeks = dt_delta["weeks"]
                    # Get dt range given assembled arguments
                    if hour == "*":
                        dt_range = general_utils.get_dt_range(
                            dt, days=input_days, hours=input_hours,
                            weeks=input_weeks)
                    else:
                        dt_range = general_utils.get_dt_range(
                            datetime.datetime(
                                dt.year, dt.month, dt.day, hour=int(hour)),
                            days=input_days, hours=input_hours,
                            weeks=input_weeks)
                    # Exclude hours
                    if exclude_hours:
                        dt_range = general_utils.exclude_hours_from_range(
                            dt_range, exclude_hours)
                    # Assemble list of valid s3 paths
                    for dt_object in dt_range:
                        dt_path = path.format(
                            date_str=dt.date(), dt=dt_object,
                            dt_m1=dt_object - datetime.timedelta(days=1),
                            dt_p1=dt_object + datetime.timedelta(days=1),
                            hour=dt_object.hour,
                            lz_hour=general_utils.leading_zero(dt_object.hour),
                            bucket=bucket, **unique_format_args)
                        # Only check whether path exists if the bucket matches
                        # TODO: Update this once bucket asset is setup properly
                        if bucket in dt_path:
                            exist_status = s3_utils.check_s3_path(
                                S3_ACCESS_KEY, S3_SECRET_KEY, dt_path, bucket)
                        else:
                            # Assume we are using IAM role to read
                            exist_status = s3_utils.check_s3_path(
                                None, None, *s3_utils.parse_url(dt_path))
                        # Verify whether path exists if bucket matches and is
                        # new then append
                        if (
                            exist_status and
                            (dt_path not in dataset_s3_path_list)
                        ):
                            dataset_s3_path_list.append(dt_path)
                # Otherwise, get latest valid path
                elif dt_delta["delta_type"] == "latest":
                    # Default to one
                    latest_days = 1
                    if "days" in dt_delta:
                        latest_days = dt_delta["days"]
                    n = 1 + latest_days
                    i = 0
                    for day_diff in range(n):
                        dataset_s3_path = path.format(
                            date_str=dt.date() - datetime.timedelta(
                                days=day_diff),
                            dt=dt - datetime.timedelta(days=day_diff),
                            dt_m1=dt - datetime.timedelta(days=day_diff + 1),
                            dt_p1=dt - datetime.timedelta(days=day_diff - 1),
                            hour=hour,
                            lz_hour=general_utils.leading_zero(hour),
                            bucket=bucket, **unique_format_args)
                        # Only check whether path exists if the bucket matches
                        exist_status = True
                        if bucket in dataset_s3_path:
                            exist_status = s3_utils.check_s3_path(
                                S3_ACCESS_KEY, S3_SECRET_KEY, dataset_s3_path,
                                bucket)
                        # Set to previous date if the path isn't valid
                        if exist_status:
                            break
                        i += 1
                    if i == n:
                        logging.error(f"No latest path exists for {dataset_s3_path}\n")
                    else:
                        dataset_s3_path_list.append(dataset_s3_path)
                else:
                    logging.error("Invalid dt_delta arguments provided.\n")

        return dataset_s3_path_list


    def _load_data_from_s3(
            self, column_headers, column_types, file_format, separator,
            header, rename={}):
        """
        This method will load the dataset into a pyspark DataFrame object
        and set corresponding meta data.

        Returns:
            pyspark DataFrame
        """
        # Explicitely raise exception if no valid files were found
        if not self.file_path_list:
            logging.error("No valid data located.\n")
            raise Exception
        # Otherwise attempt to load data
        if file_format == "csv":
            df = self.spark.read.load(
                self.file_path_list, format=file_format, sep=separator,
                header=header, schema=spark_utils.create_spark_schema(
                    column_headers, column_types))
        elif file_format in ("parquet", "delta", "avro"):
            df = self.spark.read.load(
                self.file_path_list, format=file_format, mergeSchema=True)
        elif file_format == "json":
            df = self.spark.read.json(self.file_path_list)
        # Rename columns if applicable
        if rename:
            df = spark_utils.rename_cols(self.df, rename)

        return df
