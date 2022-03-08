import pytest

from bookmark.tests.factories import BookmarkFactory

pytestmark = pytest.mark.django_db


def test_get_tags(bookmark):

    tags = bookmark[0].get_tags()
    assert tags == "django, video"

    tags = bookmark[1].get_tags()
    assert tags == "django"


def test_get_favicon_url(monkeypatch_bookmark):

    bookmark = BookmarkFactory(url="https://www.bordercore.com")

    url = bookmark.get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark.url = "http://www.bordercore.com"
    url = bookmark.get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark.url = "http://www.bordercore.com/path"
    url = bookmark.get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark.url = "bordercore.com/path"
    url = bookmark.get_favicon_url()
    assert url == ""
