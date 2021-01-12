import factory
from faker import Factory as FakerFactory

from django.db.models import signals

from feed.models import Feed, FeedItem

faker = FakerFactory.create()


@factory.django.mute_signals(signals.post_save)
class FeedItemFactory(factory.DjangoModelFactory):

    class Meta:
        model = FeedItem

    title = faker.text()
    link = faker.url()


@factory.django.mute_signals(signals.post_save)
class FeedFactory(factory.DjangoModelFactory):

    class Meta:
        model = Feed

    name = faker.text()
    url = factory.LazyAttribute(lambda _: faker.url())
    homepage = faker.domain_name()

    @factory.post_generation
    def create_feed_items(obj, create, extracted, **kwargs):
        FeedItemFactory(feed=obj)
        FeedItemFactory(feed=obj)
        FeedItemFactory(feed=obj)
