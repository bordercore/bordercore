import os

import pytest

import django

from drill.models import EFACTOR_DEFAULT

django.setup()

from django.contrib.auth.models import User  # isort:skip
from drill.models import Question  # isort:skip
from tag.models import Tag  # isort:skip


@pytest.fixture(scope="function")
def question(user):

    tag, _ = Tag.objects.get_or_create(name="django")
    question = Question.objects.create(
        question="What the first element in the periodic table?",
        answer="Hydrogen",
        efactor=EFACTOR_DEFAULT,
        user=user
    )

    question.tags.add(tag)

    yield question
