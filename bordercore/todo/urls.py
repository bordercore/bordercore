"""
URL configuration for the Todo app.

This module defines all URL routes for managing Todo items, including:
- listing all todos or a specific todo by UUID
- sorting and reordering within tag lists
- moving a todo to the top of its tag list
- rescheduling a todo’s due date
"""

from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
    path(
        route="move_to_top/",
        view=views.move_to_top,
        name="move_to_top"
    ),
    path(
        route="sort/",
        view=views.sort_todo,
        name="sort"
    ),
    path(
        route="",
        view=views.TodoListView.as_view(),
        name="list"
    ),
    path(
        route="get_tasks",
        view=views.TodoTaskList.as_view(),
        name="get_tasks"
    ),
    path(
        route="reschedule_task",
        view=views.reschedule_task,
        name="reschedule_task"
    ),
    path(
        route="<uuid:uuid>",
        view=views.TodoListView.as_view(),
        name="detail"
    ),
]
