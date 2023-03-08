import factory
from faker import Factory as FakerFactory

from accounts.tests.factories import UserFactory
from drill.models import Question

faker = FakerFactory.create()


class QuestionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Question

    question = faker.text()
    answer = faker.text()
    times_failed = faker.pyint(max_value=50)
    user = factory.SubFactory(UserFactory)
