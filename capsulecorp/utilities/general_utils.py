"""
Utility metohds that aren't directly related to some sort of software package
or service.
"""
import datetime
import itertools
import numpy as np
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


def pooled_stddev(stddevs, sample_sizes):
    """
    This method will calculate the pooled standard deviation across a
    group of samples given each samples standard deviation and size.

    Source: https://www.statisticshowto.com/pooled-standard-deviation/

    Args:
        stddevs (numpy.ndarray): standard deviations of samples
        sample_sizes (numpy.ndarray): samples sizes

    Returns:
        pooled stddev
    """
    return np.sqrt(np.sum([
        (sample_sizes[i] - 1) * np.power(stddevs[i], 2)
        for i in range(len(sample_sizes))
    ]) / (np.sum(sample_sizes) - len(sample_sizes)))


def test_normal(values, alpha=0.05):
    """
    This method will test whether distributions are guassian.

    Args:
        values (np.array):

    Return:
        boolean result
    """
    _, shapiro_p = shapiro(values)
    _, normal_p = normaltest(values)

    return np.all([p < alpha for p in (shapiro_p, normal_p)])
