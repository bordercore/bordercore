import pytest

from tag.models import Tag  # isort:skip
from accounts.models import SortOrderUserTag  # isort:skip


@pytest.fixture(scope="function")
def sort_order(user):

    tag1, _ = Tag.objects.get_or_create(name="tag1")
    tag2, _ = Tag.objects.get_or_create(name="tag2")
    tag3, _ = Tag.objects.get_or_create(name="tag3")

    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag1)
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag2)
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag3)
    sort_order.save()
