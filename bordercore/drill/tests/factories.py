import factory
from faker import Factory as FakerFactory

from django.contrib.auth.models import User
from django.db.models import signals

from drill.models import EFACTOR_DEFAULT, Question

faker = FakerFactory.create()


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = "testuser"


@factory.django.mute_signals(signals.post_save)
class QuestionFactory(factory.DjangoModelFactory):

    class Meta:
        model = Question

    question = faker.text()
    answer = faker.text()
    times_failed = faker.pyint(max_value=50)
    efactor = EFACTOR_DEFAULT
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
