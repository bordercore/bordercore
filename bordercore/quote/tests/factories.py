import factory
from faker import Factory as FakerFactory

from accounts.tests.factories import UserFactory
from quote.models import Quote

faker = FakerFactory.create()


class QuoteFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Quote

    quote = faker.text(max_nb_chars=200)
    source = faker.text(max_nb_chars=32)
    user = factory.SubFactory(UserFactory)
