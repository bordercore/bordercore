from django.urls import path

from . import views

app_name = "homepage"

urlpatterns = [
    path(
        route="",
        view=views.homepage,
        name="homepage"
    ),
    path(
        route="get_calendar_events/",
        view=views.get_calendar_events,
        name="get_calendar_events"
    ),
    path(
        route="gallery",
        view=views.gallery,
        name="gallery"
    ),
]
