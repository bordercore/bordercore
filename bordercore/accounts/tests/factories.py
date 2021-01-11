import factory

from django.contrib.auth.models import User
from django.db.models import signals

from accounts.models import UserProfile

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "testuser@bordercore.com"


@factory.django.mute_signals(signals.post_save)
class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ("username", "email")

    username = TEST_USERNAME
    password = factory.PostGenerationMethodCall("set_password", TEST_PASSWORD)
    email = TEST_PASSWORD

    @factory.post_generation
    def create_userprofile(obj, create, extracted, **kwargs):

        UserProfile.objects.get_or_create(
            user=obj,
            theme="light"
        )
