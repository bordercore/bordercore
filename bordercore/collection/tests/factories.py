import factory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from collection.models import Collection


@factory.django.mute_signals(signals.post_save)
class CollectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: f"collection_{n}")
    user = factory.SubFactory(UserFactory)
