# Adapted from
# http://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python

import datetime
import re

import pytz


def cleanup(interval, time_unit):

    interval = int(interval)

    if interval == 1:
        return "1 {} ago".format(time_unit)
    else:
        return "{} {}s ago".format(interval, time_unit)


def get_relative_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now(pytz.timezone('US/Eastern'))
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif type(time) is str:
        # Try with microseconds, then try without
        try:
            diff = now - datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            diff = now - datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z')
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return cleanup(second_diff, "second")
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return cleanup(second_diff / 60, "minute")
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return cleanup(second_diff / 3600, "hour")
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return cleanup(day_diff, "day")
    if day_diff < 31:
        return cleanup(day_diff / 7, "week")
    if day_diff < 365:
        return cleanup(day_diff / 30, "month")
    return cleanup(day_diff / 365, "year")


def get_date_from_pattern(pattern):
    """
    The input is expected to be an Elasticsearch date range
    dictionary, eg {"gte": <date>, "lte": <date>}.
    We only look at the "gte" part to get the date.
    """
    if pattern is None:
        return None

    date = pattern.get("gte", None)

    if date is None:
        return None

    if re.compile(r'^\d\d\d\d-\d\d-\d\d$').match(date):
        return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')
    elif re.compile(r'^\d\d\d\d-\d\d$').match(date):
        return datetime.datetime.strptime(date, '%Y-%m').strftime('%B %Y')
    elif re.compile(r'^\d\d\d\d$').match(date):
        return date
    elif re.compile(r'^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d').match(date):
        return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').strftime('%B %d, %Y')
    elif re.compile(r'^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d').match(date):
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y, %I:%M %p').replace("PM", "p.m.").replace("AM", "a.m.")
    else:
        matches = re.compile(r'^\[([-\d]*) TO ([-\d]*)\]$').match(date)
        if matches:
            return "{} to {}".format(matches.group(1), matches.group(2))

    return date
