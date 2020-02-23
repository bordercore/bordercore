import os
from pathlib import PurePath
import string


def get_missing_ids(expected, found):

    found_ids = [int(x["_id"].split("_")[-1]) for x in found["hits"]["hits"]]

    missing = [str(x.id) for x in expected if x.id not in found_ids]

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
