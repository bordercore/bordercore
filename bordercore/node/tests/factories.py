import factory
from faker import Factory as FakerFactory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from node.models import Node

faker = FakerFactory.create()


@factory.django.mute_signals(signals.post_save)
class NodeFactory(factory.DjangoModelFactory):

    class Meta:
        model = Node

    name = factory.Sequence(lambda n: f"node_{n}")
    user = factory.SubFactory(UserFactory)
    note = faker.text()
