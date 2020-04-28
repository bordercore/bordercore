# Adapted from
# http://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python

import datetime
import re
from collections import OrderedDict

import pytz


def cleanup(interval, time_unit):

    interval = int(interval)

    if interval == 1:
        return "1 {} ago".format(time_unit)
    else:
        return "{} {}s ago".format(interval, time_unit)


def get_relative_date(time=False):
    """
    Get a datetime string and return a pretty string like 'an hour ago',
    'Yesterday', '3 months ago', 'just now', etc
    """

    now = datetime.datetime.now(pytz.timezone("US/Eastern"))

    # Try with microseconds, then try without
    try:
        diff = now - datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        diff = now - datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

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


def parse_date_format_1(input_date, matcher):
    """
    Parse a date like '01/01/18'
    """
    return datetime.datetime.strptime(input_date, '%m/%d/%y')


def parse_date_format_2(input_date, matcher):
    """
    Parse a date like '01/01/2018'
    """
    return datetime.datetime.strptime(input_date, '%m/%d/%Y')


def parse_date_format_3(input_date, matcher):
    """
    Parse a date like 'Jan 01, 2018'
    """
    return datetime.datetime.strptime('{}/{}/{}'.format(matcher.group(1),
                                                        matcher.group(2),
                                                        matcher.group(3)),
                                      '%b/%d/%Y')


def parse_date_format_4(input_date, matcher):
    """
    Parse a date like 'January 01, 2018'
    """
    return datetime.datetime.strptime('{}/{}/{}'.format(matcher.group(1),
                                                        matcher.group(2),
                                                        matcher.group(3)),
                                      '%B/%d/%Y')


def parse_date_format_5(input_date, matcher):
    """
    Parse a date like '2020-01-12'
    """
    return datetime.datetime.strptime('{}/{}/{}'.format(matcher.group(2),
                                                        matcher.group(3),
                                                        matcher.group(1)),
                                      '%m/%d/%Y')


def parse_date_from_string(input_date):
    # The order of these regexes is important!
    # We need 'Feb' to match before 'February', for example, so that the
    #  right 'parse_date_' function is called

    pdict = OrderedDict()

    # 01/01/99
    pdict[r"(\d+)/(\d+)/(\d\d)$"] = parse_date_format_1

    # 01/01/1999
    pdict[r"(\d+)/(\d+)/(\d\d\d\d)$"] = parse_date_format_2

    # Jan 1, 1999
    pdict[r"(\w\w\w)\.?\s+(\d+),?\s+(\d+)$"] = parse_date_format_3

    # January 1, 1999
    pdict[r"(\w+)\.?\s+(\d+),?\s+(\d+)$"] = parse_date_format_4

    # 1999-01-01
    pdict[r"(\d\d\d\d)-(\d+)-(\d+)$"] = parse_date_format_5

    response = ''

    # Remove extraneous characters
    # eg "August 12th, 2001" becomes "August 12, 2001"
    input_date = re.sub(r"(\d+)(?:nd|rd|st|th)", r"\1", input_date)
    for key, value in pdict.items():
        m = re.compile(key).match(input_date)
        if m:
            response = value(input_date, m).strftime("%Y-%m-%d")

    return response
