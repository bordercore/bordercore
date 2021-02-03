import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_metrics_list(auto_login_user, metrics):

    _, client = auto_login_user()

    url = urls.reverse("metrics:list")
    resp = client.get(url)

    assert resp.status_code == 200
