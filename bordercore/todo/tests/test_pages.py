import time

import pytest

from django.urls import reverse

try:
    from .pages.todo import TodoPage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.mark.parametrize("login", [reverse("todo:list")], indirect=True)
def test_todo(todo, login, live_server, browser, settings):

    page = TodoPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    assert page.title_value() == "Bordercore :: Bordercore"

    # There should be initially one medium task visible
    assert page.todo_count() == 1

    # Select 'Medium' to toggle the selection and reveal all tasks
    medium_priority_filter = page.medium_priority_filter()
    medium_priority_filter.click()

    # Wait for the browser to refresh after the click
    time.sleep(1)

    # There should now be three todo tasks
    assert page.todo_count() == 3

    # Get the first todo task text
    assert page.todo_task_text() == "task_2"

    # Sort by priority to find the most important task
    assert page.sort_by_priority() == "task_1"


@pytest.mark.parametrize("login", [reverse("todo:list")], indirect=True)
def test_todo_no_fixtures(login, live_server, browser, settings):

    page = TodoPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    assert page.title_value() == "Bordercore :: Bordercore"

    # There should be no todo tasks, just a "No tasks found" message
    assert page.todo_count() == 1

    # Get the first todo task text
    assert page.todo_no_tasks_text() == "No tasks found"
