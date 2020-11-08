from django.urls import path

from . import views

app_name = "todo"

urlpatterns = [
    path(
        route="add/",
        view=views.TodoCreateView.as_view(),
        name="add"
    ),
    path(
        route="edit/<uuid:uuid>/",
        view=views.TodoDetailView.as_view(),
        name="edit"
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
]
