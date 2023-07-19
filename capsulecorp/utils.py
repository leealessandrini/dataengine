"""
Capsule Corp Utilities Module

TODO: Break this up into a subpackage and separate the methods logically into
different modules.
"""
import os
import datetime
import itertools
import numpy as np
import pandas as pd
from scipy.stats import shapiro, normaltest


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
    if isinstance(raw_dict, dict) and (len(raw_dict) > 0):
        # Make sure all values are lists
        dict_of_lists = {}
        for key, value in raw_dict.items():
            if not isinstance(value, list):
                dict_of_lists[key] = [value]
            else:
                dict_of_lists[key] = value
        # Create all unique permutations
        keys, values = zip(*dict_of_lists.items())
        dict_permutations = [
            dict(zip(keys, v)) for v in itertools.product(*values)]

    return dict_permutations


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


def pooled_stddev(stddevs, n):
    """
        This method will calculate the pooled standard deviation across a
        group of samples given each samples standard deviation and size.

        Source: https://www.statisticshowto.com/pooled-standard-deviation/

        Args:
            stddevs (numpy.ndarray): standard deviations of samples
            n (numpy.ndarray): samples sizes

        Returns:
            pooled stddev
    """
    return np.sqrt(np.sum([
        (n[i] - 1) * np.power(stddevs[i], 2)
        for i in range(len(n))]) / (np.sum(n) - len(n)))


def get_null_columns(df):
    """
        This function will get null columns.

        Args:
            df (pandas.core.frame.DataFrame): pandas DataFrame

        Returns:
            list of non null columns
    """
    return [
        column_header
        for column_header, is_null in df.isnull().all().iteritems()
        if is_null]


def get_non_null_columns(df):
    """
        This function will get non null columns.

        Args:
            df (pandas.core.frame.DataFrame): pandas DataFrame

        Returns:
            list of non null columns
    """
    return [
        column_header
        for column_header, is_null in df.isnull().all().iteritems()
        if not is_null]


def test_normal(values, alpha=0.05):
    """
        This method will test whether distributions are guassian.

        Args:
            values (np.array):

        Return:
            boolean result
    """
    shapiro_stat, shapiro_p = shapiro(values)
    normal_stat, normal_p = normaltest(values)
    is_normal = np.all([p < alpha for p in (shapiro_p, normal_p)])

    return is_normal


def collapse_dataframe_columns(df):
    """
        This method will collapse DataFrame column values into a list.

        Args:
            df (pandas.DataFrame): pandas DataFrame

        Returns:
            list of unique column values
    """
    return list(set(itertools.chain.from_iterable([
        df[~df[col].isnull()][col].values.tolist() for col in df.columns])))


def filter_dataframe(
        df, cols, filter_out=False, use_substring=False,
        use_startswith=False):
    """
        This method will filter a DataFrame by a list of columns.

        Args:
            df (pandas.DataFrame): pandas DataFrame
            cols (list): list of desired columns
            filter_out (bool): switch to filter columns out of DataFrame
            use_substring (bool): switch to use substring logic
            use_startswith (bool): switch to use startswith logic

        Returns:
            filtered DataFrame
    """
    # Create condition lambda function
    if use_substring:
        f = lambda c: any(str(substring) in c for substring in cols)
    elif use_startswith:
        f = lambda c: any(c.startswith(substring) for substring in cols)
    else:
        f = lambda c: c in cols
    # Return DataFrame with filtered columns
    if filter_out:
        return df.loc[:, [c for c in df.columns if not f(c)]]
    else:
        return df.loc[:, [c for c in df.columns if f(c)]]
