import pytest

import django

from bookmark.models import Bookmark

pytestmark = pytest.mark.data_quality

django.setup()


def test_sortordertagbookmark_exists():
    """
    Every bookmark with a tag must have a representative SortOrderTagBookmark object.
    """

    bookmarks = Bookmark.objects.filter(tags__isnull=False, sortordertagbookmark__isnull=True)

    assert len(bookmarks) == 0, f"Tagged bookmark isn't present in SortOrderTagBookmark, bookmark_id={bookmarks.first().id}, tag={bookmarks.first().tags.first()}"
