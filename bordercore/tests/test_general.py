import os

import pytest
from bs4 import BeautifulSoup

import django
from django.conf import settings

pytestmark = pytest.mark.data_quality

django.setup()


def test_no_inline_styles():
    """
    Test that there are no inline CSS styles in any template
    """

    # Collect all the templates used by Django
    template_list = []
    for template_dir in (settings.TEMPLATES[0]["DIRS"]):
        for base_dir, dirnames, filenames in os.walk(template_dir):
            for filename in filenames:
                template_list.append(os.path.join(base_dir, filename))

    for template in template_list:

        with open(template, "r") as file:
            page = file.read().replace("\n", "")

        soup = BeautifulSoup(page, "lxml")

        # Look for any tag with a "style" attribute
        count = soup.find_all(attrs={"style": True})

        # If there is only one violation and it occurs in the "body"
        #  tag, assume it's the inline background-image style,
        #  which we're accepting for now for lack of a better place
        #  to put it, given the STATIC_URL Django variable used.
        if len(count) == 1 and "body" in [x.name for x in count]:
            continue

        assert len(count) == 0, f"Found inline CSS style in template {template}"
