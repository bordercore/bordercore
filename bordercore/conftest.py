import pytest

import django

django.setup()

from tag.tests.factories import TagFactory  # isort:skip
from todo.tests.factories import TodoFactory, UserFactory  #isort:skip
from django.contrib.auth.models import User  # isort:skip


@pytest.fixture(scope="function")
def user(db):
    user = User.objects.create(username="testuser")
    yield user


@pytest.fixture()
def django_user():

    return UserFactory()


@pytest.fixture()
def todo_factory():

    task_1 = TodoFactory(priority=1)
    task_2 = TodoFactory(priority=1)
    task_3 = TodoFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    task_1.tags.add(tag_1)
    task_2.tags.add(tag_2)
