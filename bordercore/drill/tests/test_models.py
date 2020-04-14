import os

import pytest

import django
from django.conf import settings
from django.core.files import File

from drill.models import EASY_BONUS, EFACTOR_DEFAULT, INTERVAL_MODIFIER

from drill.models import Question  # isort:skip

django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip


def test_get_tags(question):

    assert question.get_tags() == "django"


def test_get_state_name(question):

    assert Question.get_state_name("N") == "New"
    assert Question.get_state_name("L") == "Learning"
    assert Question.get_state_name("R") == "To Review"
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
