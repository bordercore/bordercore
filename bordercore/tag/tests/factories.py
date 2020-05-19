import factory

from tag.models import Tag


class TagFactory(factory.DjangoModelFactory):

    class Meta:
        model = Tag
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"tag_{n}")
