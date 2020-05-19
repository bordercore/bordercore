import factory

from django.contrib.auth.models import User
from django.db.models import signals

from todo.models import Todo


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = "testuser"
    # username = factory.Faker("user_name")


@factory.django.mute_signals(signals.post_save)
class TodoFactory(factory.DjangoModelFactory):

    class Meta:
        model = Todo

    task = factory.Sequence(lambda n: f"task_{n}")
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
