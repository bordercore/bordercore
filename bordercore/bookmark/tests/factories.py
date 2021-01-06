import factory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from bookmark.models import Bookmark


@factory.django.mute_signals(signals.post_save)
class BookmarkFactory(factory.DjangoModelFactory):

    class Meta:
        model = Bookmark

    title = factory.Sequence(lambda n: f"Bookmark {n}")
    url = "https://www.bordercore.com"
    user = factory.SubFactory(UserFactory)
