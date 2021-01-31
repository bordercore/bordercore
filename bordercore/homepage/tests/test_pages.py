import pytest

from django.urls import reverse

try:
    from .pages.homepage import HomePage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.mark.parametrize("login", [reverse("homepage:homepage")], indirect=True)
def test_homepage(bookmark, todo, login, live_server, browser, settings):

    settings.DEBUG = True

    page = HomePage(browser)

    assert page.title_value() == "Bordercore :: Homepage"

    # There should be two important todo tasks
    assert page.todo_count() == 2

    # There should be two recent untagged bookmarks
    assert page.bookmarks_count() == 2

    # There should be one pinned bookmark
    assert page.pinned_bookmarks_count() == 1
