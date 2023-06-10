from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
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
