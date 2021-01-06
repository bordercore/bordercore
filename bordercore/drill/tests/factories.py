import factory
from faker import Factory as FakerFactory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from drill.models import EFACTOR_DEFAULT, Question

faker = FakerFactory.create()


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
