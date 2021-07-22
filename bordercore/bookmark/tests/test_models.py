import pytest

pytestmark = pytest.mark.django_db


def test_get_tags(bookmark):

    tags = bookmark[0].get_tags()
    assert tags == "django, video"

    tags = bookmark[1].get_tags()
    assert tags == "django"


def test_get_favicon_url(bookmark):

    url = bookmark[0].get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark[0].url = "http://www.bordercore.com"
    url = bookmark[0].get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark[0].url = "http://www.bordercore.com/path"
    url = bookmark[0].get_favicon_url()
    assert url == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    bookmark[0].url = "bordercore.com/path"
    url = bookmark[0].get_favicon_url()
    assert url == ""
