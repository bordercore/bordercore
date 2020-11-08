from django.urls import path

from . import views

app_name = "fitness"

urlpatterns = [
    path(
        route="add/<int:exercise_id>/",
        view=views.fitness_add,
        name="add"
    ),
    path(
        route="change_active_status/",
        view=views.change_active_status,
        name="change_active_status"
    ),
    path(
        route="<int:exercise_id>/",
        view=views.ExerciseDetailView.as_view(),
        name="exercise_detail"
    ),
    path(
        route="",
        view=views.fitness_summary,
        name="summary"
    ),
]
