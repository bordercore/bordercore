import factory

from django.db.models import signals

from accounts.tests.factories import UserFactory
from todo.models import Todo


@factory.django.mute_signals(signals.post_save)
class TodoFactory(factory.DjangoModelFactory):

    class Meta:
        model = Todo

    name = factory.Sequence(lambda n: f"task_{n}")
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):

        if not create:
            return
