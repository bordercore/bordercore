import pytest

from lib.time_utils import parse_date_from_string


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
