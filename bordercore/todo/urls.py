from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
    path(
        route="create/",
        view=views.TodoCreateView.as_view(),
        name="create"
    ),
    path(
        route="update/<uuid:uuid>/",
        view=views.TodoDetailView.as_view(),
        name="update"
    ),
    path(
        route="delete/<uuid:uuid>/",
        view=views.TodoDeleteView.as_view(),
        name="delete"
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
        route="<str:tag_name>",
        view=views.TodoTaskList.as_view(),
        name="list_tasks"
    ),
]
