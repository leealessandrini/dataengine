"""
Apache Spark Utility Methods
"""
import pyspark.sql.types as ps_types


def create_spark_schema(column_headers, column_types):
    """
    This method will create the pyspark schema provited types and
    column headers.

    Returns:
        pyspark schema
    """
    columns = zip(column_headers, column_types)
    schema = ps_types.StructType([
        ps_types.StructField(
            col_name,
            getattr(ps_types, col_type)(),
            True)
        for (col_name, col_type) in columns])

    return schema


def rename_cols(spark_df, column_map):
    """
    This method will rename a spark dataframes columns provided a column map.

    Args:
        spark_df (pyspark.sql.dataframe.DataFrame): data
        column_map (dict): rename column mapping

    Returns:
        modified spark dataframe with new column headers
    """
    for old_col_header, new_col_header in column_map.items():
        spark_df = spark_df.withColumnRenamed(
            old_col_header, new_col_header)

    return spark_df


def get_equivalent_spark_type(pandas_type):
    """
    This method will retrieve the corresponding spark type given a pandas
    type.

    Source: https://stackoverflow.com/questions/37513355

    Args:
        pandas_type (str): pandas data type

    Returns:
        spark data type
    """
    type_map = {
        'datetime64[ns]': ps_types.TimestampType(),
        'int64': ps_types.LongType(),
        'int32': ps_types.IntegerType(),
        'float64': ps_types.DoubleType(),
        'float32': ps_types.FloatType()}
    if pandas_type not in type_map:
        return ps_types.StringType()

    return type_map[pandas_type]


def pandas_to_spark(spark, pandas_df):
    """
    This method will return a spark dataframe given a pandas dataframe.

    Args:
        spark (pyspark.sql.session.SparkSession): pyspark session
        pandas_df (pandas.core.frame.DataFrame): pandas DataFrame

    Returns:
        equivalent spark DataFrame
    """
    columns = list(pandas_df.columns)
    types = list(pandas_df.dtypes)
    p_schema = ps_types.StructType([
        ps_types.StructField(column, get_equivalent_spark_type(pandas_type))
        for column, pandas_type in zip(columns, types)])

    return spark.createDataFrame(pandas_df, p_schema)


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
