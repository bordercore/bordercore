from django.urls import path

from . import views

app_name = "quote"

urlpatterns = [
    path(
        route="random",
        view=views.get_random_quote,
        name="random"
    ),
]
