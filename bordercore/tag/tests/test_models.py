import pytest

import django
from django.db.utils import IntegrityError

django.setup()

from tag.models import TagBookmark, Tag  # isort:skip

pytestmark = pytest.mark.django_db


def test_tag_check_no_commas_constraint(auto_login_user, tag):
    """
    Test the constraint that prohibits tags with commas in their name
    """

    user, _ = auto_login_user()

    with pytest.raises(IntegrityError):
        Tag.objects.create(user=user, name="tag,name")


def test_reorder(bookmark, tag):

    # Move the first bookmark down the list, from 1 -> 2
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 3

    # Move the same bookmark down the list again, from 2 -> 3
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(3)
    assert tbso.sort_order == 3

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 2

    # Move the same bookmark back to the top of the list
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 2

    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 3

    # Move the last bookmark to the top of the list
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    assert tbso.sort_order == 2

    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 3


def test_delete(bookmark, tag):

    # Delete the first bookmark
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.delete()

    # Verify that the last two bookmarks have a new sort order (decrease by one)
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 2

    # Delete the new first bookmark
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    tbso.delete()

    # Verify that the last bookmark has sort_order = 1
    tbso = TagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 1


def test_pin(auto_login_user, tag):

    user, _ = auto_login_user()

    tag[0].pin()

    assert tag[0] in user.userprofile.pinned_tags.all()


def test_unpin(auto_login_user, tag):

    user, _ = auto_login_user()

    tag[0].pin()
    tag[0].unpin()

    assert tag[0] not in user.userprofile.pinned_tags.all()
