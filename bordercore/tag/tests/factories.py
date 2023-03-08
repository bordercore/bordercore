import factory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from tag.models import Tag


@factory.django.mute_signals(signals.post_save)
class TagFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Tag
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"tag_{n}")
    user = factory.SubFactory(UserFactory)
