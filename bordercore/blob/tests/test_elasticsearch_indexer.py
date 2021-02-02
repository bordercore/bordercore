from pathlib import Path

import psycopg2
import pytest
from elasticsearch_dsl import Range

from blob.elasticsearch_indexer import (DB_ENDPOINT, DB_PASSWORD, DB_USERNAME,
                                        get_blob_info, get_doctype,
                                        get_num_pages, get_range_from_date,
                                        get_unixtime_from_string,
                                        is_ingestible_file)

# def test_get_doctype(blob_image_factory, blob_text_factory):

#     assert get_doctype(blob_image_factory, None) == "blob"
#     assert get_doctype(blob_text_factory, None) == "document"


def test_is_ingestible_file():

    assert is_ingestible_file("foobar.pdf") is True
    assert is_ingestible_file("foobar.mp4") is False


def test_get_unixtime_from_string():

    assert get_unixtime_from_string(None) is None
    assert get_unixtime_from_string("") is None
    assert get_unixtime_from_string("2021-03-01 14:52:23") == "1614628343"
    assert get_unixtime_from_string("2021-03-01") == "1614574800"
    assert get_unixtime_from_string("2021-03") == "1614574800"
    assert get_unixtime_from_string("2021") == "1609477200"
    assert get_unixtime_from_string("[2021-03 TO 2021-04]") == "1614574800"

    with pytest.raises(ValueError):
        get_unixtime_from_string("March 1, 2021")


def test_get_doctype():

    blob = {"is_note": True}
    assert get_doctype(blob, {}) == "note"

    blob = {"is_note": ""}
    metadata = {"is_book": True}
    assert get_doctype(blob, metadata) == "book"

    blob = {"sha1sum": True, "is_note": ""}
    assert get_doctype(blob, {}) == "blob"

    blob = {"sha1sum": None, "is_note": ""}
    assert get_doctype(blob, {}) == "document"


def test_get_range_from_date():

    date = "2021-03-01"
    assert get_range_from_date(date) == Range(gte=date, lte=date)

    date1 = "2021-03"
    date2 = "2021-04"
    date = f"[{date1} TO {date2}]"
    assert get_range_from_date(date) == Range(gte=date1, lte=date2)


def test_get_num_pages():

    filepath = Path(__file__).parent / "resources/test_blob.pdf"

    with open(filepath, "rb") as fh:
        contents = fh.read()

    assert get_num_pages(contents) == 18
