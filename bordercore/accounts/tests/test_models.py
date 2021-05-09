import pytest

from django.contrib.auth.models import User

from accounts.models import SortOrderUserTag, pinned_tags_has_changed
from accounts.tests.factories import TEST_USERNAME

pytestmark = pytest.mark.django_db


def test_get_tags(sort_order_user_tag):

    user = User.objects.get(username=TEST_USERNAME)

    assert user.userprofile.get_tags() == "django, video, linux"


def test_reorder(sort_order_user_tag, tag):

    user = User.objects.get(username=TEST_USERNAME)

    tags = user.userprofile.pinned_tags.all().order_by("sortorderusertag__sort_order")

    # New order: 2, 3, 1
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag[1])
    SortOrderUserTag.reorder(s, 1)

    tags = user.userprofile.pinned_tags.all().order_by("sortorderusertag__sort_order")

    assert tags[0] == tag[1]
    assert tags[1] == tag[2]
    assert tags[2] == tag[0]
    assert len(tags) == 3

    # New order: 1, 3, 2
    s = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag[2])
    SortOrderUserTag.reorder(s, 3)
    tags = user.userprofile.pinned_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag[1]
    assert tags[1] == tag[0]
    assert tags[2] == tag[2]
    assert len(tags) == 3

    # Delete tag2, so we're left with 1, 3
    sort_order = SortOrderUserTag.objects.get(userprofile=user.userprofile, tag=tag[2])
    sort_order.delete()
    tags = user.userprofile.pinned_tags.all().order_by("sortorderusertag__sort_order")
    assert tags[0] == tag[1]
    assert tags[1] == tag[0]
    assert len(tags) == 2


def test_pinned_tags_has_changed():

    assert pinned_tags_has_changed("django", "django") is False
    assert pinned_tags_has_changed("django ", "django") is False
    assert pinned_tags_has_changed("django,linux", "django,linux") is False
    assert pinned_tags_has_changed("django, linux", "django,linux") is False
    assert pinned_tags_has_changed("linux,django", "django,linux") is False
    assert pinned_tags_has_changed("linux, django", "django,linux") is False
    assert pinned_tags_has_changed("linux, django,postgresql", "django,linux") is True
    assert pinned_tags_has_changed("linux, django,postgresql", "") is True
    assert pinned_tags_has_changed("", "linux, django,postgresql") is True
