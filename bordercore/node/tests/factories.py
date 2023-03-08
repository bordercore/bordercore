import factory
from faker import Factory as FakerFactory

from accounts.tests.factories import UserFactory
from node.models import Node

faker = FakerFactory.create()


class NodeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Node

    name = factory.Sequence(lambda n: f"node_{n}")
    user = factory.SubFactory(UserFactory)
    note = faker.text()
