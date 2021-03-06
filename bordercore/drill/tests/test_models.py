import re
from datetime import timedelta

import factory
import pytest

from django.db.models import signals

from .factories import QuestionFactory

from drill.models import Question, EFACTOR_DEFAULT  # isort:skip

pytestmark = pytest.mark.django_db


def test_get_tags(question):

    tags = question.get_tags()
    assert tags == "django, video"


def test_get_state_name(question):

    assert Question.get_state_name("N") == "New"
    assert Question.get_state_name("L") == "Learning"
    assert Question.get_state_name("R") == "Reviewing"
    assert Question.get_state_name("X") is None


def test_get_question(question):

    assert question.get_question() == f"<p>{question.question}</p>"


def test_get_answer(question):

    assert question.get_answer() == f"<p>{question.answer}</p>"


def test_get_learning_count_step(question):

    assert question.get_learning_step_count() == 2


def test_is_final_learning_step(question):

    assert question.is_final_learning_step() is False

    question.learning_step = 2
    assert question.is_final_learning_step() is True


def test_learning_step_increase(question):

    assert(question.learning_step == question.LEARNING_STEPS[0][0])
    question.learning_step_increase()
    assert(question.learning_step == question.LEARNING_STEPS[1][0])
    question.learning_step_increase()
    assert(question.learning_step == question.LEARNING_STEPS[1][0])


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
