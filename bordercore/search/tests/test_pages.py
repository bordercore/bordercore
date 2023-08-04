import time

import pytest

from django.urls import reverse

try:
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys

    from .pages.search import NoteSearchPage, SearchPage, TagSearchPage
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

    # Select "Exact Match" search to "Yes", since there could be more
    #  than one result, and our first test requires only one.
    select = page.exact_match_select()
    select.select_by_visible_text("Yes")
    submit_button = page.submit_button()
    submit_button.click()

    # Test the number of matches
    assert page.search_result_count() == 1

    assert page.search_result_name() == blob_image_factory[0].name

    # Test the number of tags for the search result
    assert page.search_result_tag_count() == 3

    # Get the tag names for the search result
    tag_list = page.search_result_tags()
    assert set([x.name for x in blob_image_factory[0].tags.all()]) == set([x.strip() for x in tag_list])


@pytest.mark.parametrize("login", [reverse("search:kb_search_tag_detail_search")], indirect=True)
def test_tag_search(blob_text_factory, login, live_server, browser, settings):

    page = TagSearchPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    search_input = page.search_input()
    search_input.send_keys("django")
    time.sleep(1)
    search_input.send_keys(Keys.DOWN)
    search_input.send_keys(Keys.ENTER)

    # Count the number of search results
    time.sleep(2)
    assert page.search_tag_result_count() == 3


@pytest.mark.parametrize("login", [reverse("homepage:homepage")], indirect=True)
def test_note_search(blob_note, login, live_server, browser, settings):

    page = NoteSearchPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    # Click the search icon to reveal the search dialog box
    top_search_icon = page.top_search_icon()
    top_search_icon.click()

    time.sleep(1)

    search_input = page.search_input()
    # Search for the first two words from the note's title
    search_input.send_keys(" ".join(blob_note[0].name.split()[:2]))

    # Enable note filter
    action = ActionChains(browser)
    action.move_to_element(search_input)
    action.key_down(Keys.ALT).send_keys("n").perform()
    action.reset_actions()

    time.sleep(2)
    search_input.send_keys(Keys.RETURN)

    time.sleep(2)
    assert page.search_result_count() == 1
