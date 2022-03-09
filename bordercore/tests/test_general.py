import os

import pytest
from bs4 import BeautifulSoup

import django
from django.conf import settings

pytestmark = pytest.mark.data_quality

django.setup()


def test_html():
    """
    Look for HTML that violates best practices, such as inline styles
    and temporary attributes.
    """

    # Collect all the templates used by Django or Vue
    template_list = []
    dir_list = [
        settings.TEMPLATES[0]["DIRS"],
        [f"{os.environ['BORDERCORE_HOME']}/front-end/vue"]
    ]

    for template_dir in ([item for sublist in dir_list for item in sublist]):
        for base_dir, dirnames, filenames in os.walk(template_dir):
            for filename in filenames:
                template_list.append(os.path.join(base_dir, filename))

    for template in template_list:

        with open(template, "r") as file:
            page = file.read().replace("\n", "")

        soup = BeautifulSoup(page, "lxml")

        # Look for any inline CSS styles, ie a tag with a "style" attribute
        count = soup.find_all(attrs={"style": True})

        # If there is only one violation and it occurs in the "body"
        #  tag, assume it's the inline background-image style,
        #  which we're accepting for now for lack of a better place
        #  to put it, given the STATIC_URL Django variable used.
        if len(count) == 1 and "body" in [x.name for x in count]:
            continue

        assert len(count) == 0, f"Found inline CSS style in template {template}"

        # Look for any tag with a "_class" attribute
        count = soup.find_all(attrs={"_class": True})

        assert len(count) == 0, f"Found a tag with attribute name '_class' in template {template}"

        # Look for any classes with an underscore in the name
        count = soup.select("div[class*='_']")

        assert len(count) == 0, f"Found a class name starting with '_' in template {template}"
