import factory
from factory.fuzzy import FuzzyInteger
from faker import Factory as FakerFactory

from accounts.tests.factories import UserFactory
from music.models import Album, Artist, Playlist, Song, SongSource

faker = FakerFactory.create()


class ArtistFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Artist

    name = factory.Sequence(lambda n: f"artist_{n}")
    user = factory.SubFactory(UserFactory)


class AlbumFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Album

    title = factory.Sequence(lambda n: f"album_{n}")
    artist = factory.SubFactory(ArtistFactory, user=factory.SelfAttribute("..user"))
    year = FuzzyInteger(1970, 2020)
    user = factory.SubFactory(UserFactory)


class SongSourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SongSource

    name = factory.Sequence(lambda n: f"songsource_{n}")
    description = faker.text()


class SongFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Song

    title = factory.Sequence(lambda n: f"song_{n}")
    artist = factory.SubFactory(ArtistFactory, user=factory.SelfAttribute("..user"))
    album = factory.SubFactory(AlbumFactory, user=factory.SelfAttribute("..user"))
    track = FuzzyInteger(1, 10)
    year = FuzzyInteger(1970, 2020)
    source = factory.SubFactory(SongSourceFactory)
    length = FuzzyInteger(100, 400)
    user = factory.SubFactory(UserFactory)


class PlaylistFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Playlist

    name = factory.Sequence(lambda n: f"playlist_{n}")
    size = FuzzyInteger(1, 50)
    type = "manual"
    user = factory.SubFactory(UserFactory)
