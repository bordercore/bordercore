import string
from pathlib import PurePath

import requests
from lxml import html


def get_missing_blob_ids(expected, found):

    found_ids = [x["_id"] for x in found["hits"]["hits"]]

    missing = [str(x.uuid) for x in expected if str(x.uuid) not in found_ids]
    return ", ".join(missing)


def get_missing_bookmark_ids(expected, found):

    found_ids = [x["_id"].split("_")[-1] for x in found["hits"]["hits"]]

    missing = [str(x.id) for x in expected if str(x.id) not in found_ids]
    return ", ".join(missing)


def remove_non_ascii_characters(input_string, default="Default"):
    """
    Remove all non ASCII characters from string. If the entire string consists
    of non ASCII characters, return the "default" value.
    """

    output_string = "".join(filter(lambda x: x in string.printable, input_string))

    if not output_string:
        output_string = default

    return output_string


# Putting these two functions here rather than in blob/models.py so
#  that AWS lambdas can easily re-use them

def is_image(file):

    if file:
        file_extension = PurePath(str(file)).suffix
        if file_extension[1:].lower() in ["gif", "jpg", "jpeg", "png"]:
            return True
    return False


def is_pdf(file):

    if file:
        file_extension = PurePath(str(file)).suffix
        if file_extension[1:].lower() in ["pdf"]:
            return True
    return False


def get_pagination_range(current_page_num, num_pages, paginate_by):
    """
    Get a range of pages based on the current page and the maximum number
    of pages, used for a navigation UI.
    """

    max_pagination_range = 5

    x = range(current_page_num - paginate_by, current_page_num + paginate_by + 1)

    if x[0] <= 0:
        x = range(1, min(max_pagination_range, num_pages) + 1)

    if x[-1] - (paginate_by - 1) >= num_pages:
        x = range(x[0] - paginate_by, max(max_pagination_range, num_pages) + 1)

    return list(x)


def parse_title_from_url(url):

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
