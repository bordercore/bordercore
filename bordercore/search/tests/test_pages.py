import time

import pytest

from django.urls import reverse

try:
    from .pages.search import SearchPage, TagSearchPage
    from selenium.webdriver.common.keys import Keys
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
    search_input.send_keys(blob_image_factory[0].name)
    submit_button = page.submit_button()
    submit_button.click()

    # Test the number of matches
    assert page.search_result_count() == "5"

    assert page.search_result_name() == blob_image_factory[0].name

    # Test the number of tags for the search result
    assert page.search_result_tag_count() == 12

    # Get the tag names for the search result
    tag_list = page.search_result_tags()
    assert set([x.name for x in blob_image_factory[0].tags.all()]) == set(tag_list)


@pytest.mark.parametrize("login", [reverse("search:kb_search_tag_detail_search")], indirect=True)
def test_tag_search(blob_text_factory, login, live_server, browser, settings):

    page = TagSearchPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    search_input = page.search_input()
    search_input.send_keys("django" + Keys.ENTER)

    # Count the number of search results
    time.sleep(1)
    assert page.search_tag_result_count() == 3


@pytest.mark.parametrize("login", [reverse("homepage:homepage")], indirect=True)
def test_note_search(blob_text_factory, login, live_server, browser, settings):

    page = NoteSearchPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    search_input = page.search_input()
    search_input.send_keys("django")

    # Specify notes search
    action = ActionChains(browser)
    action.move_to_element(search_input)
    action.key_down(Keys.ALT).send_keys("n").perform()

    search_input.send_keys(Keys.RETURN)

    assert page.search_result_count() == 3
