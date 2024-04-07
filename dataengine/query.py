import os
import datetime
import string
from marshmallow import Schema, fields, post_load, validates, ValidationError
from dataengine import dataset
from .utilities import general_utils


class MyFormatter(string.Formatter):
    """
    Custom formatter class from stackoverflow.com/questions/17215400
    """
    def __init__(self, default='{{{0}}}'):
        self.default = default

    def get_value(self, key, args, kwds):
        if isinstance(key, str):
            return kwds.get(key, self.default.format(key))
        else:
            return string.Formatter.get_value(key, args, kwds)


class IntermittentTablesSchema(Schema):
    """
    Schema for specifying the SQL statement information.
    """
    table_name = fields.String(required=True)
    filename = fields.String(required=True)
    format_args = fields.Dict()

    @validates("filename")
    def validate_filename(self, filename):
        """
        Validate the SQL filepath by checking whether it exists.
        """
        if not os.path.exists(filename):
            raise ValidationError(f"Invalid filename provided: {filename}")


class SqlInfoSchema(Schema):
    """
    Schema for specifying the SQL statement information.
    """
    filename = general_utils.StringOrListField(required=True)
    format_args = fields.Dict()
    intermittent_tables = fields.List(fields.Nested(IntermittentTablesSchema))

    @validates("filename")
    def validate_filename(self, filename):
        """
        Validate the SQL filepath by checking whether it exists.
        """
        # Setup file list
        if isinstance(filename, str):
            file_list = [filename]
        else:
            file_list = filename
        # Validate each SQL file provided
        for file_path in file_list:
            if not os.path.exists(file_path):
                raise ValidationError(
                    f"Invalid filename provided: {file_path}")


class DependencySchema(Schema):
    """
    Schema for specifying the dependencies of the Query object.
    """
    table_name = fields.String(required=True)
    base_dataset = fields.String(required=True)
    format_args = fields.Dict()
    time_delta = fields.Nested(dataset.TimeDeltaSchema)
    timestamp_conversion = fields.List(
        fields.Nested(dataset.TimestampConversionSchema))
    dt_delta = fields.Nested(dataset.DtDeltaSchema)
    exclude_hours = fields.List(fields.String())


class DeleteInfoSchema(Schema):
    """
    Schema for specifying the database table delete parameters.
    """
    delete_all = fields.Boolean()
    days = fields.Integer()
    column_header = fields.String()


class LoadInfoSchema(Schema):
    """
    Schema for specifying the database load information.
    """
    load_location = fields.String(required=True)
    db_arg = fields.String(required=True)
    table_name = fields.String(required=True)
    delete_info = fields.Nested(DeleteInfoSchema)
    replace = fields.Boolean()
    truncate = fields.Boolean(missing=False)

    # TODO: Validate load location using assets
    @validates("load_location")
    def validate_load_location(self, load_location):
        """
        valid_args = []
        if load_location not in valid_args:
            raise ValidationError(
                f"Invalid load_location '{load_location}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))
        """
        pass


class DistinctVariableSchema(Schema):
    """
    Distinct Variable marshallow validation schema.
    """
    variable_name = fields.String(required=True)
    table_name = fields.String(required=True)
    column_header = fields.String(required=True)
    lower = fields.Boolean()


class ReplaceWhereSchema(Schema):
    """
    Delta Replace Where arguments for the s3 write.
    """
    column_header = fields.String(required=True)
    column_value = fields.String(required=True)


class Repartition(Schema):
    """
    Spark repartition arguments.
    """
    n_partitions = fields.Integer()
    column_headers = fields.List(fields.String())


class QuerySchema(Schema):
    """
    Query marshmallow validation schema.
    """
    dt = fields.DateTime(required=True)
    hour = fields.String(required=True)
    sql_info = fields.Nested(SqlInfoSchema, required=True)
    # TODO: Move ouput arguments to Nested schema
    output = fields.String(required=True)
    file_format = fields.String()
    separator = fields.String()
    use_pandas = fields.Boolean()
    header = fields.Boolean()
    partition_by = fields.List(fields.String())
    repartition = fields.Nested(Repartition)
    replace_where = fields.List(fields.Nested(ReplaceWhereSchema))
    mode = fields.String()
    max_records_per_file = fields.Integer()
    exact_records_per_file = fields.Integer()
    # Setup nested schemas for dependencies, load, and delete information
    dependencies = fields.List(fields.Nested(DependencySchema), required=True)
    load_info = fields.Nested(LoadInfoSchema)
    # Setup distict column values variables
    distinct_variables = fields.List(fields.Nested(DistinctVariableSchema))

    @post_load
    def create_query(self, input_data, **kwargs):
        return Query(**input_data)

    @validates("mode")
    def validate_mode(self, mode):
        valid_args = ["overwrite", "append"]
        if mode not in valid_args:
            raise ValidationError(
                f"Invalid mode '{mode}' provided, "
                "please choose among the list: [{}]".format(
                    ", ".join(valid_args)))


class Query(object):
    """
    Query class.
    """
    def __init__(
            self, dt, hour, sql_info, output, dependencies, load_info={},
            file_format="csv", separator=",", header=True, use_pandas=False,
            partition_by=[], repartition={}, replace_where=[],
            distinct_variables=[], mode="overwrite",
            max_records_per_file=None, exact_records_per_file=None,
            **kwargs
        ):
        """
            Query constructor.
        """
        # Format date and hour strings
        date_str = str(dt.date())
        if hour == "*":
            dt_str = str(dt)
        else:
            dt_str = str(datetime.datetime(
                dt.year, dt.month, dt.day, int(hour)))
        # Set default arguments
        self.output = output.format(dt=dt, date_str=date_str, hour=hour)
        self.file_format = file_format
        self.separator = separator
        self.use_pandas = use_pandas
        self.header = header
        self.dependencies = dependencies
        self.load_info = load_info
        self.intermittent_tables = []
        self.distinct_variables = distinct_variables
        self.mode = mode
        self.max_records_per_file = max_records_per_file
        self.exact_records_per_file = exact_records_per_file
        # Setup partitioning arguments
        self.partition_by = partition_by
        self.repartition = repartition
        if replace_where:
            self.replace_where = self._setup_replace_where(
                replace_where, date_str, dt_str)
        else:
            self.replace_where = replace_where
        # Load SQL file and format query
        if isinstance(sql_info["filename"], str):
            self.file_path_list = [sql_info["filename"]]
        else:
            self.file_path_list = sql_info["filename"]
        self.format_args = {}
        if "format_args" in sql_info:
            self.format_args = sql_info["format_args"]
        self.sql = self._load_sql(
            dt, date_str, dt_str, hour, self.file_path_list, self.format_args)
        # Setup intermittent tables if provided
        if "intermittent_tables" in sql_info:
            self.intermittent_tables = sql_info["intermittent_tables"]
            for i in range(len(self.intermittent_tables)):
                if "format_args" in self.intermittent_tables[i]:
                    format_args = self.intermittent_tables[i]["format_args"]
                else:
                    format_args = {}
                self.intermittent_tables[i]["sql"] = self._load_sql(
                    dt, date_str, dt_str, hour, [self.intermittent_tables[i]["filename"]],
                    format_args)


    def _load_sql(self, dt, date_str, dt_str, hour, file_path_list, format_args):
        """
        This method will load the query and format all arguments.

        Args:
            base_dir (str): base file directory
            dt (datetime.datetime): date information
            hour (Union[str|int]): hour information
            file_path_list (list): list of relative file paths
            format_args (dict): extra string formating args for query

        Returns:
            query string
        """
        sql_list = []
        for file_path in file_path_list:
            # Read sql from file and format string
            query = open(file_path, "r").read()
            # Format string using custom formatter
            fmt = MyFormatter()
            query = fmt.format(
                query, dt=dt, date_str=date_str, dt_str=dt_str, hour=hour,
                **format_args)
            # Append to list
            sql_list.append(query)

        return "\n\nUNION ALL\n\n".join(sql_list)

    def _setup_replace_where(self, replace_where, date_str, dt_str):
        """
            This method will setup the delta replace where argument.

            Args:
                replace_where (list): replace where arguments
                date_str (str): date string
                dt_str (str): datetime string

            Returns:
                formatted replace_where arguments
        """
        formatted_replace_where = []
        for key_value_pair in replace_where:
            formatted_replace_where.append(
                "{column_header} == '{column_value}'".format(
                    column_header=key_value_pair["column_header"],
                    column_value=key_value_pair["column_value"].format(
                        date_str=date_str, dt_str=dt_str)))

        return formatted_replace_where
