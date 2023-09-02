"""
Utility metohds that aren't directly related to some sort of software package
or service.
"""
import datetime
import itertools
import logging
import math
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


def leading_zero(hour):
    """
    This method will generate an hour str with a leading zero.

    Args:
        hour (int|str): hour

    Returns:
        leading zero digit str
    """
    str_hour = str(hour)
    if ((len(str_hour) == 1) and (str_hour != "*")):
        str_hour = "0" + str_hour

    return str_hour


def get_dt_range(dt, days=1, hours=0, weeks=0):
    """
    This method will generate the date range between the provided datetime
    and days / hours. Subtract hours / days when negative, otherwise add
    them.

    Args:
        dt (datetime.datetime): input datetime
        days (int): number of days
        hours (int): number of hours

    Returns:
        date range list
    """
    # If both values passed in are 0 return input datetime
    if (days == 0) and (hours == 0) and (weeks == 0):
        logging.error("Both days, hours, and weeks arguments were all 0.")
        return [dt]
    # If hour passed in is the glob character adjust accordingly
    if hours == "*":
        # If days are negative set the dt hour to 23
        if days < 0:
            dt = datetime.datetime(dt.year, dt.month, dt.day, 23)
        # Set hours to 0
        hours = 0
        # Set days to 1 if 0 was passed in
        days = (1 if days == 0 else days)
    # If weeks is setup grab trailing weeks
    if weeks != 0:
        dt_range = [
            dt - datetime.timedelta(weeks=minus_week)
            for minus_week in range(1, weeks + 1)]
    else:
        # Combine days and hours
        total_hours = (24 * days) + hours
        # Get dt range
        if total_hours < 0:
            dt_range = [
                dt - datetime.timedelta(hours=hour)
                for hour in range(abs(total_hours))]
        else:
            dt_range = [
                dt + datetime.timedelta(hours=hour)
                for hour in range(total_hours)]

    return dt_range


def exclude_hours_from_range(dt_range, exclude_hours):
    """
    This method will take a list of strings, convert them to a list of
    integers, then remove all datetimes from the range where the hour
    matches any in the list of integers.

    Args:
        dt_range (list): list of datetimes
        exclude_hours (list): list of strings

    Returns:
        modified list with hours excluded
    """
    hours = []
    # Assemble list of hours
    for arg in exclude_hours:
        # Get range if - in argument
        if "-" in arg:
            hours += np.arange(
                *[int(i) for i in arg.split("-")]).tolist()
        # Otherwise cast the character to an int and append
        else:
            hours.append(int(arg))
    # Update the dt range to exclude these hours and return
    return [i for i in dt_range if i.hour not in hours]


def create_time_string(total_time):
    """
    This method will create a time string given total seconds.

    Args:
        total_time (str): total time in seconds

    Returns:
        time string
    """
    minutes = math.floor(total_time / 60.0)
    minutes_str = "{minutes} minute{s}".format(
        minutes=minutes, s="s" * (minutes != 1))
    seconds = total_time % 60
    seconds_str = "{seconds} second{s}".format(
        seconds=seconds, s="s" * (seconds != 1))
    time_str = (
        minutes_str * (minutes != 0) +
        " and " * (minutes != 0 and seconds != 0) +
        seconds_str * (seconds != 0))

    return time_str


def apply_time_delta(dt, hour, time_delta):
    """
    This method will apply the time delta arguments to the dt and hour
    objects needed for formatting dataset paths.

    Args:
        dt (datetime.datetime): datetime object
        hour (str): either the hour or a glob of all hours
        time_delta (dict): dict with hours and days fields

    Returns:
        new modified datetime and hour objects
    """
    # If hour is glob only consider time delta day arguments
    if hour == "*":
        td = datetime.timedelta(
            **{k: v for k, v in time_delta.items() if k == "days"})
        new_dt = dt - td
        new_hour = hour
    # Otherwise cast hour to int, setup dt, and subtract full time delta
    else:
        td = datetime.timedelta(**time_delta)
        new_dt = datetime.datetime(dt.year, dt.month, dt.day, int(hour)) - td
        new_hour = new_dt.hour

    return new_dt, new_hour


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
