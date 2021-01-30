import pytest

import django

django.setup()

from tag.models import SortOrderTagBookmark, Tag  # isort:skip

pytestmark = pytest.mark.django_db


def test_reorder(bookmark, tag):

    # Move the first bookmark down the list, from 1 -> 2
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other two bookmarks have changed their sort order
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 3

    # Move the same bookmark down the list again, from 2 -> 3
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(3)
    assert tbso.sort_order == 3

    # Verify that the other two bookmarks have changed their sort order
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 2

    # Move the same bookmark back to the top of the list
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 2

    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 3

    # Move the last bookmark to the top of the list
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    assert tbso.sort_order == 2

    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 3


def test_delete(bookmark, tag):

    # Delete the first bookmark
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[0])
    tbso.delete()

    # Verify that the last two bookmarks have a new sort order (decrease by one)
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    assert tbso.sort_order == 1

    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 2

    # Delete the new first bookmark
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[1])
    tbso.delete()

    # Verify that the last bookmark has sort_order = 1
    tbso = SortOrderTagBookmark.objects.get(tag=tag[0], bookmark=bookmark[2])
    assert tbso.sort_order == 1


def test_search(tag, auto_login_user):

    user, _ = auto_login_user()

    assert tag[0].name in [x["text"] for x in Tag.search(user, "djang")]
    assert len(Tag.search(user, "djang")) == 1

    assert len(Tag.search(user, "postg")) == 0
    assert len(Tag.search(user, "djang", True)) == 0


def test_add_favorite_tag(auto_login_user, tag):

    user, _ = auto_login_user()

    tag[0].add_favorite_tag()

    assert tag[0] in user.userprofile.favorite_tags.all()


def test_remove_favorite_tag(auto_login_user, tag):

    user, _ = auto_login_user()

    tag[0].add_favorite_tag()
    tag[0].remove_favorite_tag()

    assert tag[0] not in user.userprofile.favorite_tags.all()
