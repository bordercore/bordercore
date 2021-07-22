import pytest

from django import urls

from homepage import views

pytestmark = [pytest.mark.django_db, pytest.mark.views]


@pytest.fixture
def monkeypatch_homepage(monkeypatch):
    """
    Prevent the homepage view from interacting with Elasticsearch by
    patching out the 'get_random_image' function.
    """

    def mock(*args, **kwargs):
        pass

    monkeypatch.setattr(views, "get_random_blob", mock)


def test_homepage(monkeypatch_homepage, auto_login_user, bookmark, question, todo):

    _, client = auto_login_user()

    url = urls.reverse("homepage:homepage")
    resp = client.get(url)

    assert resp.status_code == 200
