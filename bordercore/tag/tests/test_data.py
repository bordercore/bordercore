import pytest

import django
from django.db.models import OuterRef, Subquery

from bookmark.models import Bookmark
from tag.models import Tag, TagAlias, TagBookmark

pytestmark = pytest.mark.data_quality

django.setup()


def test_tagbookmark_exists():
    """
    Every bookmark with a tag must have a representative TagBookmark object.
    """

    bookmarks = Bookmark.objects.filter(tags__isnull=False, tagbookmark__isnull=True)

    assert len(bookmarks) == 0, f"Tagged bookmark isn't present in TagBookmark, bookmark_id={bookmarks.first().id}, tag={bookmarks.first().tags.first()}"


def test_tagbookmark_and_tag_exists():
    """
    For every TagBookmark object, the corresponding bookmark must also
    have the corresponding tag.
    """

    tagbookmarks = TagBookmark.objects.exclude(
        tag__in=Subquery(
            Bookmark.objects.filter(
                pk=OuterRef("bookmark")
            ).values(
                "tags"
            )
        )
    )

    assert len(tagbookmarks) == 0, f"TagBookmark id={tagbookmarks.first().pk} exists, but bookmark id={tagbookmarks.first().bookmark.id} does not have tag id={tagbookmarks.first().tag.id} ({tagbookmarks.first().tag})"


def test_tag_alias():
    """
    There should be no tags that match any tag aliases.
    """
    tag_aliases = TagAlias.objects.all()

    for alias in tag_aliases:
        assert not Tag.objects.filter(user=alias.user, name=alias.name), \
            f"Tag {alias.name} exists as an alias for user {alias.user}."
