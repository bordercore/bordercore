import pytest

from tag.tests.factories import TagFactory

from .factories import QuestionFactory


@pytest.fixture(scope="function")
def question(user):

    question = QuestionFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    question.tags.add(tag_1)
    question.tags.add(tag_2)

    yield question
