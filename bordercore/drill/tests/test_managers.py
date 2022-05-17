import pytest

from drill.models import Question
from drill.tests.factories import QuestionFactory
from tag.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def test_recent_tags(auto_login_user):

    user, _ = auto_login_user()

    question_0 = QuestionFactory()
    question_1 = QuestionFactory()

    tag_0 = TagFactory()
    tag_1 = TagFactory()
    question_0.tags.add(tag_0)
    question_0.tags.add(tag_1)
    question_0.save()

    tag_2 = TagFactory()
    question_1.tags.add(tag_2)
    question_1.save()

    recent_tags = Question.objects.recent_tags(user)[:2]

    assert tag_1.name in [x["name"] for x in recent_tags]
    assert tag_2.name in [x["name"] for x in recent_tags]
    assert tag_0.name not in [x["name"] for x in recent_tags]
