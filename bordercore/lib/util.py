import os
import string
from pathlib import PurePath

import requests


def get_elasticsearch_connection(host=None):

    # Isolate the import here so other functions from this module
    #  can be imported without requiring these dependencies.
    from elasticsearch import RequestsHttpConnection
    from elasticsearch_dsl.connections import connections

    if not host:
        host = os.environ.get("ELASTICSEARCH_ENDPOINT", "localhost")

    return connections.create_connection(
        hosts=[host],
        use_ssl=False,
        timeout=1200,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )


def get_missing_blob_ids(expected, found):

    found_ids = [x["_id"] for x in found["hits"]["hits"]]

    missing = [str(x.uuid) for x in expected if str(x.uuid) not in found_ids]
    return ", ".join(missing)


def get_missing_bookmark_ids(expected, found):

    found_ids = [x["_source"]["uuid"].split("_")[-1] for x in found["hits"]["hits"]]

    missing = [str(x.uuid) for x in expected if str(x.uuid) not in found_ids]
    return ", ".join(missing)


def get_missing_metadata_ids(expected, found):

    found_ids = [x["_id"] for x in found["hits"]["hits"]]

    missing = set([str(x.blob.uuid) for x in expected if str(x.blob.uuid) not in found_ids])
    return ", ".join(missing)


def truncate(string, limit=100):

    return string[:limit] + ("..." if len(string) > limit else "")


def remove_non_ascii_characters(input_string, default="Default"):
    """
    Remove all non ASCII characters from string. If the entire string consists
    of non ASCII characters, return the "default" value.
    """

    output_string = "".join(filter(lambda x: x in string.printable, input_string))

    if not output_string:
        output_string = default

    return output_string


# Putting these functions here rather than in blob/models.py so
#  that AWS lambdas can easily re-use them

def is_image(file):

    if file:
        file_extension = PurePath(str(file)).suffix
        if file_extension[1:].lower() in ["bmp", "gif", "jpg", "jpeg", "png", "tiff"]:
            return True
    return False


def is_pdf(file):

    if file:
        file_extension = PurePath(str(file)).suffix
        if file_extension[1:].lower() in ["pdf"]:
            return True
    return False


def is_video(file):

    if file:
        file_extension = PurePath(str(file)).suffix
        if file_extension[1:].lower() in ["avi", "flv", "m4v", "mkv", "mp4", "webm"]:
            return True
    return False


def get_pagination_range(page_number, num_pages, paginate_by):
    """
    Get a range of pages based on the current page and the maximum number
    of pages, used for a navigation UI.

    page_number: the current page number
    num_pages: the total number of pages in the result set
    paginate_by: the number of navigation pages to display before
                 and after the current page
    """

    # The maximum range is twice the "paginate_by" value plus 1, the current page.
    # If this exceeds the total number of pages, use that instead.
    max_range = min(num_pages, paginate_by * 2 + 1)

    # Try to create a range that extends below and above the current
    #  page by "paginate_by" number of pages.
    x = range(page_number - paginate_by, page_number + paginate_by + 1)

    if x[0] <= 0:
        # If the lower bound is below zero, create a new range that begins at one
        # and extends out to max_range or the number of pages, whichever is smaller.
        x = range(1, min(max_range, num_pages) + 1)

    if x[-1] - (paginate_by - 1) >= num_pages:
        # If the upper bound exceeds the number of pages, create a new range that
        # extends out to max_range or the number of pages, whichever is larger.
        x = range(max(1, x[0] - paginate_by), max(max_range, num_pages + 1))

    return list(x)


def parse_title_from_url(url):

    # Isolate the import here so other functions from this module
    #  can be imported without requiring these dependencies.
    from lxml import html

    headers = {"user-agent": "Bordercore/1.0"}
    r = requests.get(url, headers=headers)
    http_content = r.text.encode("utf-8")

    # http://stackoverflow.com/questions/15830421/xml-unicode-strings-with-encoding-declaration-are-not-supported
    doc = html.fromstring(http_content)
    title = doc.xpath(".//title")
    if title:
        return (r.url, title[0].text)
    else:
        return (r.url, "No title")
