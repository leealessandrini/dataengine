import os
import logging
import datetime
from marshmallow import Schema, fields, post_load, validates, ValidationError
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


class S3PathField(fields.Field):
    """
    Field to represent either a string or list of strings.

    Source: https://stackoverflow.com/questions/61614546
    """
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            return [value]
        elif (
            isinstance(value, list) and
            all([isinstance(i, str) for i in value])
        ):
            return value
        else:
            raise ValidationError('Field should be string or list of strings')


class DatasetSchema(Schema):
    """
        Dataset marshmallow validation schema.
    """
    spark = fields.Raw(required=True)
    dt = fields.DateTime(required=True)
    hour = fields.String(required=True)
    s3_path = S3PathField(required=True)
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

    @validates("file_format")
    def validate_file_format(self, file_format):
        valid_args = ["csv", "parquet", "delta", "avro", "json"]
        if file_format not in valid_args:
            raise ValidationError(
                f"Invalid file_format '{file_format}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))

    @post_load
    def create_dataset(self, input_data, **kwargs):
        return Dataset(**input_data)


class Dataset(object):
    """
    This class will function as the base class for pyspark datasets
    within the SAF.
    """

    def __init__(
            self, spark, dt, hour, s3_path, bucket,
            format_args={}, file_format="csv", column_headers=[],
            column_types=[], separator=",", header=False,
            time_delta={"days": 0, "hours": 0, "weeks": 0},
            timestamp_conversion=[], dt_delta={}, exclude_hours=[],
            rename={}, **kwargs):
        """
        Dataset constructor.
        """
        self.spark = spark
        # Get all unique permutations of the format arguments
        format_args_permutations = general_utils.get_dict_permutations(format_args)
        # Setup list of s3 paths
        self.s3_path = self._setup_s3_path(
            s3_path, dt, hour, time_delta, bucket, format_args_permutations,
            dt_delta, exclude_hours)
        # Load data into a pyspark DataFrame
        self._load_data(
            column_headers, column_types, file_format, separator, header,
            rename=rename)
        # Convert timestamp if applicable
        if timestamp_conversion:
            for params in timestamp_conversion:
                self.df = spark_utils.convert_timestamp(self.df, **params)

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
                        exist_status = True
                        if bucket in dt_path:
                            exist_status = s3_utils.check_s3_path(
                                S3_ACCESS_KEY, S3_SECRET_KEY, dt_path, bucket)
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


    def _load_data(
            self, column_headers, column_types, file_format, separator,
            header, rename={}):
        """
        This method will load the dataset into a pyspark DataFrame object
        and set corresponding meta data.

        Returns:
            pyspark DataFrame
        """
        # Explicitely raise exception if no valid files were found
        if not self.s3_path:
            logging.error("No valid data located.\n")
            raise Exception
        # Otherwise attempt to load data
        self.file_format = file_format
        if file_format == "csv":
            self.df = self.spark.read.load(
                self.s3_path, format=self.file_format, sep=separator,
                header=header, schema=spark_utils.create_spark_schema(
                    column_headers, column_types))
        elif file_format in ("parquet", "delta", "avro"):
            self.df = self.spark.read.load(
                self.s3_path, format=self.file_format, mergeSchema=True)
        elif file_format == "json":
            self.df = self.spark.read.json(self.s3_path)
        # Rename columns if applicable
        if rename:
            self.df = spark_utils.rename_cols(self.df, rename)
        # Setup column header, type, and schema variables
        self.column_headers = self.df.columns
        self.column_types = [i.dataType for i in self.df.schema]
        self.schema = self.df.schema
