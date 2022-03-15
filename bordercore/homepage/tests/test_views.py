from unittest.mock import MagicMock

import pytest

from django import urls

from blob.tests.factories import BlobFactory
from collection.tests.factories import CollectionFactory
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

    monkeypatch.setattr(views, "get_random_image", mock)


def test_homepage(monkeypatch_homepage, auto_login_user, bookmark, question, todo):

    _, client = auto_login_user()

    url = urls.reverse("homepage:homepage")
    resp = client.get(url)

    assert resp.status_code == 200


def test_get_random_image(auto_login_user):

    user, client = auto_login_user()

    collection = CollectionFactory(user=user)
    blob = BlobFactory(user=user)
    collection.add_blob(blob)
    user.userprofile.homepage_image_collection = collection

    mock_request = MagicMock()
    mock_request.user = user

    image = views.get_random_image(mock_request)

    assert image["name"] == blob.name
    assert image["uuid"] == blob.uuid
