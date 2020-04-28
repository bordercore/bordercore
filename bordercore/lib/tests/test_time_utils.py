import datetime
from unittest.mock import Mock, patch

import pytest
import pytz

from lib.time_utils import cleanup, get_relative_date, parse_date_from_string


def test_cleanup():

    assert cleanup(1, "second") == "1 second ago"
    assert cleanup(2, "hour") == "2 hours ago"


def test_get_relative_date():

    timezone = pytz.timezone("US/Eastern")
    datetime_mock = Mock(wraps=datetime.datetime)
    datetime_mock.now.return_value = timezone.localize(datetime.datetime(2020, 4, 28, 8, 0, 0))

    # Patch what datetime.now() returns with a mock
    with patch("datetime.datetime", new=datetime_mock):
        assert get_relative_date("2020-04-28T09:00:00-0400") == ""
        assert get_relative_date("2020-04-28T07:59:55-0400") == "just now"
        assert get_relative_date("2020-04-28T07:59:30-0400") == "30 seconds ago"
        assert get_relative_date("2020-04-28T07:59:00-0400") == "a minute ago"
        assert get_relative_date("2020-04-28T07:30:00-0400") == "30 minutes ago"
        assert get_relative_date("2020-04-28T07:00:00-0400") == "an hour ago"
        assert get_relative_date("2020-04-28T02:00:00-0400") == "6 hours ago"
        assert get_relative_date("2020-04-27T08:00:00-0400") == "Yesterday"
        assert get_relative_date("2020-04-25T08:00:00-0400") == "3 days ago"
        assert get_relative_date("2020-04-13T08:00:00-0400") == "2 weeks ago"
        assert get_relative_date("2020-03-13T08:00:00-0400") == "1 month ago"
        assert get_relative_date("2017-03-13T08:00:00-0400") == "3 years ago"


def test_parse_date_from_string():

    date_string = "01/01/99"
    assert parse_date_from_string(date_string) == "1999-01-01"

    date_string = "01/01/1999"
    assert parse_date_from_string(date_string) == "1999-01-01"

    date_string = "January 1, 1999"
    assert parse_date_from_string(date_string) == "1999-01-01"

    date_string = "1999-01-01"
    assert parse_date_from_string(date_string) == "1999-01-01"

    date_string = "August 12th, 2001"
    assert parse_date_from_string(date_string) == "2001-08-12"

    date_string = "Note a date"  # Should match nothing
    assert parse_date_from_string(date_string) == ""

    date_string = "Jann 1, 1999"  # Misspelling
    with pytest.raises(ValueError):
        parse_date_from_string(date_string)
