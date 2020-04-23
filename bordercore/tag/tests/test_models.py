
import django

django.setup()

from tag.models import TagBookmark, TagBookmarkSortOrder  # isort:skip


def test_reorder(user, tagbookmark, bookmarks):

    # Move the first bookmark down the list, from 1 -> 2
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    assert tbso.sort_order == 1

    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    assert tbso.sort_order == 3

    # Move the same bookmark down the list again, from 2 -> 3
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[0])
    tbso.reorder(3)
    assert tbso.sort_order == 3

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    assert tbso.sort_order == 1

    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    assert tbso.sort_order == 2

    # Move the same bookmark back to the top of the list
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    assert tbso.sort_order == 2

    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    assert tbso.sort_order == 3

    # Move the last bookmark to the top of the list
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other two bookmarks have changed their sort order
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[0])
    assert tbso.sort_order == 2

    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    assert tbso.sort_order == 3


def test_delete(user, tagbookmark, bookmarks):

    # Delete the first bookmark
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[0])
    tbso.delete()

    # Verify that the last two bookmarks have a new sort order (decrease by one)
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    assert tbso.sort_order == 1

    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    assert tbso.sort_order == 2

    # Delete the new first bookmark
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[1])
    tbso.delete()

    # Verify that the last bookmark has sort_order = 1
    tbso = TagBookmarkSortOrder.objects.get(tag_bookmark=tagbookmark, bookmark=bookmarks[2])
    assert tbso.sort_order == 1
