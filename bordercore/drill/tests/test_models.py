from datetime import timedelta

import factory
import pytest

from django.db.models import signals
from django.utils import timezone

from .factories import QuestionFactory

from drill.models import Question, EFACTOR_DEFAULT  # isort:skip

pytestmark = pytest.mark.django_db


def test_str(question):

    assert str(question[0]) == question[0].question


def test_needs_review(question):
    assert question[0].needs_review is True

    question[0].record_response("good")
    assert question[0].needs_review is False


def test_get_tags(question):

    tags = question[0].get_tags()
    assert tags == "django, video"


def test_get_state_name(question):

    assert Question.get_state_name("N") == "New"
    assert Question.get_state_name("L") == "Learning"
    assert Question.get_state_name("R") == "Reviewing"
    assert Question.get_state_name("X") is None


def test_get_learning_count_step(question):

    assert question[0].get_learning_step_count() == 2


def test_is_final_learning_step(question):

    assert question[0].is_final_learning_step() is False

    question[0].learning_step = 2
    assert question[0].is_final_learning_step() is True


def test_learning_step_increase(question):

    assert(question[0].learning_step == question[0].LEARNING_STEPS[0][0])
    question[0].learning_step_increase()
    assert(question[0].learning_step == question[0].LEARNING_STEPS[1][0])
    question[0].learning_step_increase()
    assert(question[0].learning_step == question[0].LEARNING_STEPS[1][0])


@factory.django.mute_signals(signals.post_save)
def test_record_response():

    question = QuestionFactory()

    question.record_response("good")
    assert question.state == "L"
    assert question.interval == timedelta(days=1)
    assert question.efactor == EFACTOR_DEFAULT
    assert question.learning_step == 2

    question.record_response("good")
    assert question.state == "R"
    assert question.interval == timedelta(days=2, seconds=43200)
    assert question.efactor == EFACTOR_DEFAULT
    assert question.learning_step == 2

    question.record_response("good")
    assert question.state == "R"
    assert question.interval == timedelta(days=6, seconds=21600)
    assert question.efactor == EFACTOR_DEFAULT
    assert question.learning_step == 2

    question.record_response("hard")
    assert question.state == "R"
    assert question.interval == timedelta(days=4, seconds=32400)
    assert question.efactor == 2.125
    assert question.learning_step == 2

    question.record_response("again")
    assert question.state == "L"
    assert question.interval == timedelta(days=1)
    assert question.efactor == 1.7
    assert question.learning_step == 2

    question.record_response("again")
    assert question.state == "L"
    assert question.interval == timedelta(days=1)
    assert question.efactor == 1.3599999999999999
    assert question.learning_step == 1

    question.record_response("easy")
    assert question.state == "R"
    assert question.interval == timedelta(days=1, seconds=66355, microseconds=200000)
    assert question.efactor == 1.5639999999999998
    assert question.learning_step == 1


def test_get_last_response(question):

    question[0].record_response("easy")
    question[0].record_response("good")
    assert question[0].get_last_response().response == "good"


def test_get_all_tags_progress(question):

    tags_info = question[0].get_all_tags_progress()
    assert len(tags_info) == 2


def test_start_study_session(question, tag):

    session = {}

    current = Question.start_study_session(question[0].user, session, "favorites", "review")
    assert current in [str(question[2].uuid), str(question[3].uuid)]
    assert len(session["drill_study_session"]["list"]) == 2

    current = Question.start_study_session(question[0].user, session, "tag-needing-review", "review", tag[0].name)
    assert current in [str(x.uuid) for x in question]
    assert len(session["drill_study_session"]["list"]) == 1
    assert session["drill_study_session"]["tag"] == tag[0].name

    current = Question.start_study_session(question[0].user, session, "learning", "review")
    assert current in [str(x.uuid) for x in question]
    assert len(session["drill_study_session"]["list"]) == 4

    current = Question.start_study_session(question[0].user, session, "random", "review", 3)
    assert current in [str(x.uuid) for x in question]
    assert len(session["drill_study_session"]["list"]) == 3

    first_word_of_question = question[0].question.split(" ")[0]
    current = Question.start_study_session(question[0].user, session, "search", "review", first_word_of_question)
    assert current in [str(x.uuid) for x in question]
    assert len(session["drill_study_session"]["list"]) > 1
    first_word_of_answer = question[0].question.split(" ")[0]
    current = Question.start_study_session(question[0].user, session, "search", "review", first_word_of_answer)
    assert current in [str(x.uuid) for x in question]
    assert len(session["drill_study_session"]["list"]) > 1


@factory.django.mute_signals(signals.post_save)
def test_get_tag_progress(question, tag):

    tags_info = Question.get_tag_progress(question[0].user, tag[0])
    assert str(tags_info["name"]) == "django"
    assert tags_info["progress"] == 0
    assert tags_info["last_reviewed"] == "Never"
    assert tags_info["count"] == 1

    question[0].record_response("good")

    tags_info = Question.get_tag_progress(question[0].user, tag[0])
    assert str(tags_info["name"]) == "django"
    assert tags_info["progress"] == 0
    assert tags_info["last_reviewed"] == timezone.now().strftime("%B %d, %Y")
    assert tags_info["count"] == 1

    question[0].record_response("good")

    tags_info = Question.get_tag_progress(question[0].user, tag[0])
    assert str(tags_info["name"]) == "django"
    assert tags_info["progress"] == 100
    assert tags_info["last_reviewed"] == timezone.now().strftime("%B %d, %Y")
    assert tags_info["count"] == 1

    tags_info = Question.get_tag_progress(question[0].user, tag[2])
    assert str(tags_info["name"]) == "linux"
    assert tags_info["progress"] == 0
    assert tags_info["last_reviewed"] == "Never"
    assert tags_info["count"] == 0
