from django.urls import path

from . import views

app_name = "drill"

urlpatterns = [
    path(
        route="",
        view=views.DrillListView.as_view(),
        name="list"
    ),
    path(
        route="question/delete/<int:pk>/",
        view=views.QuestionDeleteView.as_view(),
        name="delete"
    ),
    path(
        route="question/<int:question_id>/",
        view=views.QuestionDetailView.as_view(),
        name="detail"
    ),
    path(
        route="question/add/<str:tag>/",
        view=views.QuestionCreateView.as_view(),
        name="add_with_tag"
    ),
    path(
        route="question/add/",
        view=views.QuestionCreateView.as_view(),
        name="add"
    ),
    path(
        route="question/edit/<int:pk>/",
        view=views.QuestionUpdateView.as_view(),
        name="edit"
    ),
    path(
        route="question/skip/<int:question_id>/",
        view=views.skip_question,
        name="skip"
    ),
    path(
        route="search/",
        view=views.DrillSearchListView.as_view(),
        name="search"
    ),
    path(
        route="answer/<int:question_id>/",
        view=views.show_answer,
        name="answer"
    ),
    path(
        route="response/<int:question_id>/<str:response>/",
        view=views.record_response,
        name="record_response"
    ),
    path(
        route="study/random/",
        view=views.study_random,
        name="study_random"
    ),
    path(
        route="study/tag/<str:tag>/",
        view=views.study_tag,
        name="study_tag"
    ),
    path(
        route="tagsearch/",
        view=views.tag_search,
        name="tag_search"
    ),
]
