import pytest

from django.contrib.auth.models import User

from accounts.tests.factories import TEST_USERNAME
from todo.models import Todo

pytestmark = pytest.mark.django_db


def test_get_todo_counts(todo_factory):

    user = User.objects.get(username=TEST_USERNAME)
    counts = Todo.get_todo_counts(user, "tag_0")
    assert counts[0]["count"] == 3
    assert counts[1]["count"] == 1

    counts = Todo.get_todo_counts(user, "tag_1")
    assert counts[0]["count"] == 1
    assert counts[1]["count"] == 3
