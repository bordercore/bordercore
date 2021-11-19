import factory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from blob.models import Blob, MetaData
from tag.tests.factories import TagFactory


@factory.django.mute_signals(signals.post_save)
class MetaDataFactory(factory.DjangoModelFactory):

    class Meta:
        model = MetaData


class BlobFactory(factory.DjangoModelFactory):

    class Meta:
        model = Blob

    user = factory.SubFactory(UserFactory)

    content = factory.Faker("text")
    note = factory.Faker("text")

    md1 = factory.RelatedFactory(
        MetaDataFactory,
        "blob",
        name="Url",
        value="https://www.bordercore.com",
        user=user)
    md2 = factory.RelatedFactory(
        MetaDataFactory,
        "blob",
        name="Author",
        value="John Smith",
        user=user)
    md3 = factory.RelatedFactory(
        MetaDataFactory,
        "blob",
        name="Artist",
        value="John Smith",
        user=user)
    md4 = factory.RelatedFactory(
        MetaDataFactory,
        "blob",
        name="Artist",
        value="Jane Doe",
        user=user)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):

        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(TagFactory(name=tag))
