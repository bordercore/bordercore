import pytest

from tag.tests.factories import TagFactory
from todo.models import Todo

from .factories import TodoFactory


@pytest.mark.django_db
def test_get_todo_counts():

    task_1 = TodoFactory()
    task_2 = TodoFactory()
    task_3 = TodoFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    task_1.tags.add(tag_1)
    task_2.tags.add(tag_1)
    task_3.tags.add(tag_1)
    task_3.tags.add(tag_2)

    counts = Todo.get_todo_counts(task_1.user, tag_1.name)
    assert counts[0]["count"] == 3
    assert counts[1]["count"] == 1

    counts = Todo.get_todo_counts(task_1.user, tag_2.name)
    assert counts[0]["count"] == 1
    assert counts[1]["count"] == 3
