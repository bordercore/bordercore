from pathlib import Path

import pytest
import responses
from elasticsearch_dsl import Range

from api.serializers import BlobSerializer, BlobSha1sumSerializer
from blob.elasticsearch_indexer import (get_blob_info, get_doctype,
                                        get_num_pages, get_range_from_date,
                                        get_unixtime_from_string,
                                        is_ingestible_file)


def test_is_ingestible_file():

    assert is_ingestible_file("foobar.pdf") is True
    assert is_ingestible_file("foobar.mp4") is False


def test_get_blob_info(blob_image_factory):

    url = f"https://www.bordercore.com/api/blobs/{blob_image_factory[0].uuid}/"
    serializer = BlobSerializer(blob_image_factory[0])
    responses.add(responses.GET, url,
                  json=serializer.data, status=200)

    blob_info = get_blob_info(uuid=blob_image_factory[0].uuid)
    assert blob_info["name"] == blob_image_factory[0].name
    assert set(blob_info["tags"]) == set([x.name for x in blob_image_factory[0].tags.all()])
    assert set(blob_info["metadata"]) == set([x.name.lower() for x in blob_image_factory[0].metadata.all()])

    url = f"https://www.bordercore.com/api/sha1sums/{blob_image_factory[0].sha1sum}/"
    serializer = BlobSha1sumSerializer(blob_image_factory[0])
    responses.add(responses.GET, url,
                  json=serializer.data, status=200)

    blob_info = get_blob_info(sha1sum=blob_image_factory[0].sha1sum)
    assert blob_info["name"] == blob_image_factory[0].name
    assert set(blob_info["tags"]) == set([x.name for x in blob_image_factory[0].tags.all()])
    assert set(blob_info["metadata"]) == set([x.name.lower() for x in blob_image_factory[0].metadata.all()])


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
