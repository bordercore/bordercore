import factory
import responses

from django.conf import settings
from django.db.models import signals

from accounts.tests.factories import UserFactory
from api.serializers import BlobSerializer
from blob.elasticsearch_indexer import index_blob
from blob.models import Blob, MetaData
from tag.tests.factories import TagFactory


@factory.django.mute_signals(signals.post_save)
class MetaDataFactory(factory.DjangoModelFactory):

    class Meta:
        model = MetaData


class BlobFactory(factory.DjangoModelFactory):

    class Meta:
        model = Blob

    name = factory.Faker("text", max_nb_chars=30)
    user = factory.SubFactory(UserFactory)
    date = factory.Faker("date")
    content = factory.Faker("text")
    note = factory.Faker("text")

    @factory.post_generation
    def metadata(self, create, extracted, **kwargs):

        if extracted:
            for x in range(extracted):
                MetaDataFactory(
                    blob=self,
                    name=factory.Faker("text", max_nb_chars=5),
                    value=factory.Faker("text", max_nb_chars=40),
                    user=self.user
                )
        MetaDataFactory(
            blob=self,
            name="Url",
            value=factory.Faker("url"),
            user=self.user
        )

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):

        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(TagFactory(name=tag, user=self.user))

    @staticmethod
    def index_blob(blob):

        url = f"https://www.bordercore.com/api/blobs/{blob.uuid}/"
        serializer = BlobSerializer(blob)
        responses.add(responses.GET, url,
                      json=serializer.data, status=200)

        index_blob(uuid=blob.uuid, create_connection=True, extra_fields=settings.ELASTICSEARCH_EXTRA_FIELDS)
