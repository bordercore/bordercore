import factory

from accounts.tests.factories import UserFactory
from bookmark.models import Bookmark


class BookmarkFactory(factory.DjangoModelFactory):

    class Meta:
        model = Bookmark

    title = factory.Sequence(lambda n: f"Bookmark {n}")
    url = "https://www.bordercore.com"
    user = factory.SubFactory(UserFactory)
