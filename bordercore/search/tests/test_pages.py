import time

import pytest

from django.urls import reverse

try:
    from .pages.search import SearchPage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.mark.parametrize("login", [reverse("search:search")], indirect=True)
def test_search(blob_image_factory, blob_pdf_factory, login, live_server, browser, settings):

    page = SearchPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    search_input = page.search_input()
    search_input.send_keys(blob_image_factory.name)
    submit_button = page.submit_button()
    submit_button.click()

    # There should only be one match
    assert page.search_result_count() == "1"

    assert page.search_result_name() == blob_image_factory.name

    # There should be three tags for the search result
    assert page.search_result_tag_count() == 3

    # Get the tag names for the search result
    tag_list = page.search_result_tags()
    assert set([x.name for x in blob_image_factory.tags.all()]) == set(tag_list)
