import pytest

from django.contrib.auth.models import User

from accounts.models import SortOrderUserTag, favorite_tags_has_changed
from accounts.tests.factories import TEST_USERNAME
from tag.models import Tag

pytestmark = pytest.mark.django_db


def test_get_tags(sort_order_user_tag):

    user = User.objects.get(username=TEST_USERNAME)

    assert user.userprofile.get_tags() == "tag1, tag2, tag3"


def test_reorder(sort_order_user_tag):

    # Starting order: 3, 2, 1
    tag1 = Tag.objects.get(name="tag1")
    tag2 = Tag.objects.get(name="tag2")
    tag3 = Tag.objects.get(name="tag3")

    user = User.objects.get(username=TEST_USERNAME)

    # New order: 2, 3, 1
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag2)
    SortOrderUserTag.reorder(s, 1)
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag2
    assert tags[1] == tag3
    assert tags[2] == tag1
    assert len(tags) == 3

    # New order: 1, 3, 2
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag2)
    SortOrderUserTag.reorder(s, 3)
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag3
    assert tags[1] == tag1
    assert tags[2] == tag2
    assert len(tags) == 3

    # Delete tag2, so we're left with 1, 3
    sort_order = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag2)
    sort_order.delete()
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag3
    assert tags[1] == tag1
    assert len(tags) == 2


def test_favorite_tags_has_changed():

    assert favorite_tags_has_changed("django", "django") is False
    assert favorite_tags_has_changed("django ", "django") is False
    assert favorite_tags_has_changed("django,linux", "django,linux") is False
    assert favorite_tags_has_changed("django, linux", "django,linux") is False
    assert favorite_tags_has_changed("linux,django", "django,linux") is False
    assert favorite_tags_has_changed("linux, django", "django,linux") is False
    assert favorite_tags_has_changed("linux, django,postgresql", "django,linux") is True
    assert favorite_tags_has_changed("linux, django,postgresql", "") is True
    assert favorite_tags_has_changed("", "linux, django,postgresql") is True
