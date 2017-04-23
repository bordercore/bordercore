# Adapted from
# http://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python

import pytz


def cleanup(interval, time_unit):

    interval = int(interval)

    if interval == 1:
        return "1 {} ago".format(time_unit)
    else:
        return "{} {}s ago".format(interval, time_unit)

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now(pytz.timezone('US/Eastern'))
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
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
