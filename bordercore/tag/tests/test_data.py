import pytest

import django

from bookmark.models import Bookmark
from tag.models import Tag, TagAlias

pytestmark = pytest.mark.data_quality

django.setup()


def test_sortordertagbookmark_exists():
    """
    Every bookmark with a tag must have a representative SortOrderTagBookmark object.
    """

    bookmarks = Bookmark.objects.filter(tags__isnull=False, sortordertagbookmark__isnull=True)

    assert len(bookmarks) == 0, f"Tagged bookmark isn't present in SortOrderTagBookmark, bookmark_id={bookmarks.first().id}, tag={bookmarks.first().tags.first()}"


def test_tag_alias():
    """
    There should be no tags that match any tag aliases.
    """
    tag_aliases = TagAlias.objects.all()

    for alias in tag_aliases:
        assert not Tag.objects.filter(user=alias.user, name=alias.name), \
            f"Tag {alias.name} exists as an alias for user {alias.user}."
