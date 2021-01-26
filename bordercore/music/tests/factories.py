import factory
from factory.fuzzy import FuzzyInteger
from faker import Factory as FakerFactory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from music.models import Album, Song, SongSource

faker = FakerFactory.create()


class AlbumFactory(factory.DjangoModelFactory):

    class Meta:
        model = Album

    title = factory.Sequence(lambda n: f"album_{n}")
    artist = factory.Sequence(lambda n: f"artist_{n}")
    year = FuzzyInteger(1970, 2020)
    user = factory.SubFactory(UserFactory)


class SongSourceFactory(factory.DjangoModelFactory):

    class Meta:
        model = SongSource

    name = factory.Sequence(lambda n: f"songsource_{n}")
    description = faker.text()


@factory.django.mute_signals(signals.post_save)
class SongFactory(factory.DjangoModelFactory):

    class Meta:
        model = Song

    title = factory.Sequence(lambda n: f"song_{n}")
    artist = factory.Sequence(lambda n: f"artist_{n}")
    album = factory.SubFactory(AlbumFactory)
    track = FuzzyInteger(1, 10)
    year = FuzzyInteger(1970, 2020)
    source = factory.SubFactory(SongSourceFactory)
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):

        if not create:
            return
