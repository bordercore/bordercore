from tag.models import Tag  # isort:skip
from accounts.models import SortOrder  # isort:skip


def test_get_tags(user, sort_order):

    assert user.userprofile.get_tags() == "tag1, tag2, tag3"


def test_reorder(user, sort_order):

    # Starting order: 3, 2, 1
    tag1 = Tag.objects.get(name="tag1")
    tag2 = Tag.objects.get(name="tag2")
    tag3 = Tag.objects.get(name="tag3")

    # New order: 2, 3, 1
    SortOrder.reorder(user, tag2, 1)
    tags = user.userprofile.favorite_tags.all().order_by("sortorder__sort_order")
    assert tags[0] == tag2
    assert tags[1] == tag3
    assert tags[2] == tag1
    assert len(tags) == 3

    # New order: 1, 3, 2
    SortOrder.reorder(user, tag2, 3)
    tags = user.userprofile.favorite_tags.all().order_by("sortorder__sort_order")
    assert tags[0] == tag3
    assert tags[1] == tag1
    assert tags[2] == tag2
    assert len(tags) == 3

    # Delete tag2, so we're left with 1, 3
    sort_order = SortOrder.objects.get(user_profile=user.userprofile, tag=tag2)
    sort_order.delete()
    tags = user.userprofile.favorite_tags.all().order_by("sortorder__sort_order")
    assert tags[0] == tag3
    assert tags[1] == tag1
    assert len(tags) == 2
