import pytest

from tag.tests.factories import TagFactory

from .factories import TodoFactory


@pytest.fixture(scope="function")
def todo_factory():

    task_1 = TodoFactory()
    task_2 = TodoFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    task_1.tags.add(tag_1)
    task_2.tags.add(tag_2)
