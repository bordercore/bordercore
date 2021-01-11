import time

import pytest

from django.urls import reverse

try:
    from .pages.prefs import PrefsPage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.mark.parametrize("login", [reverse("accounts:prefs")], indirect=True)
def test_prefs(collection, login, live_server, browser, settings):

    settings.DEBUG = True
    COLLECTION_NAME = "collection_0"
    TAG_NAME = "tag_0"
    THEME_NAME = "dark"

    page = PrefsPage(browser)
    page.load(live_server)

    assert page.title_value() == "Bordercore :: Preferences"

    # Choose a default collection
    page.choose_default_collection(COLLECTION_NAME)

    # Choose the 'dark' theme
    page.choose_theme(THEME_NAME)

    # Add some favorite tags
    page.add_favorite_tags(TAG_NAME)

    time.sleep(1)

    # Test that preferences were successfully updated
    page.update()
    assert page.prefs_updated_message_count() == 1

    # Test that the theme was switched
    assert page.selected_theme() == THEME_NAME

    # Test that the default collection was switched
    assert page.selected_default_collection() == COLLECTION_NAME

    # Test that a favorite tag was added
    assert page.favorite_tags() == TAG_NAME
