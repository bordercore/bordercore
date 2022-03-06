import factory

from accounts.tests.factories import UserFactory
from bookmark.models import Bookmark


class BookmarkFactory(factory.DjangoModelFactory):

    class Meta:
        model = Bookmark

    name = factory.Sequence(lambda n: f"Bookmark {n}")
    url = factory.Faker("url")
    user = factory.SubFactory(UserFactory)
