import json

import pytest
from faker import Factory as FakerFactory

from django import urls

from fitness.models import Exercise

pytestmark = [pytest.mark.django_db, pytest.mark.views]

faker = FakerFactory.create()


def test_fitness_exercise_detail(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:exercise_detail", kwargs={"exercise_uuid": fitness[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_fitness_add(auto_login_user, fitness):

    _, client = auto_login_user()

    url = urls.reverse("fitness:add", kwargs={"exercise_uuid": fitness[0].uuid})
    resp = client.post(url, {
        "workout-data": json.dumps(
            [
                {"weight": 230, "reps": 7, "duration": 0},
                {"weight": 230, "reps": 6, "duration": 0},
                {"weight": 230, "reps": 5, "duration": 0},
            ]
        )
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


def test_edit_note(auto_login_user, fitness):

    _, client = auto_login_user()

    note = faker.text()

    url = urls.reverse("fitness:edit_note")
    resp = client.post(url, {
        "uuid": fitness[0].uuid,
        "note": note
    })

    assert resp.status_code == 200

    updated_exercise = Exercise.objects.get(uuid=fitness[0].uuid)
    assert updated_exercise.note == note
