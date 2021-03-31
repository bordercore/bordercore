import json

import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_fitness_exercise_detail(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:exercise_detail", kwargs={"exercise_uuid": fitness[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_fitness_add(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:add", kwargs={"exercise_uuid": fitness[0].uuid})
    resp = client.post(url, {
        "workout-data": json.dumps([[230, 7], [230, 6], [230, 5]])
    })

    assert resp.status_code == 302


def test_fitness_summary(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:summary")
    resp = client.get(url)

    assert resp.status_code == 200


def test_fitness_change_active_status(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:change_active_status")

    resp = client.post(url, {
        "uuid": fitness[0].uuid,
        "remove": "true"
    })

    assert resp.status_code == 200

    resp = client.post(url, {
        "uuid": fitness[0].uuid
    })

    assert resp.status_code == 200
