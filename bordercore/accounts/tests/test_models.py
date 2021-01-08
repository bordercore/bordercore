import pytest

from django.contrib.auth.models import User

from accounts.models import SortOrderUserTag, favorite_tags_has_changed
from accounts.tests.factories import TEST_USERNAME
from tag.tests.factories import TagFactory

# from tag.models import Tag

pytestmark = pytest.mark.django_db


def test_get_tags(sort_order_user_tag):

    user = User.objects.get(username=TEST_USERNAME)

    assert user.userprofile.get_tags() == "tag1, tag2, tag3"


def test_reorder(sort_order_user_tag):

    # Starting order: 3, 2, 1
    tag_1 = TagFactory(name="tag1")
    tag_2 = TagFactory(name="tag2")
    tag_3 = TagFactory(name="tag3")

    user = User.objects.get(username=TEST_USERNAME)

    # New order: 2, 3, 1
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag_2)
    SortOrderUserTag.reorder(s, 1)
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag_2
    assert tags[1] == tag_3
    assert tags[2] == tag_1
    assert len(tags) == 3

    # New order: 1, 3, 2
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag_2)
    SortOrderUserTag.reorder(s, 3)
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag_3
    assert tags[1] == tag_1
    assert tags[2] == tag_2
    assert len(tags) == 3

    # Delete tag2, so we're left with 1, 3
    sort_order = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag_2)
    sort_order.delete()
    tags = user.userprofile.favorite_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag_3
    assert tags[1] == tag_1
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
