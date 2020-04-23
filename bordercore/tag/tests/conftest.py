import datetime

import pytest

import django

django.setup()

from django.contrib.auth.models import User  # isort:skip
from collection.models import Collection  # isort:skip
from bookmark.models import Bookmark  # isort:skip
from tag.models import Tag, TagBookmark, TagBookmarkSortOrder  # isort:skip


@pytest.fixture(scope="function")
def tagbookmark(user):

    tag = Tag.objects.create(name="django")

    tagbookmark = TagBookmark.objects.create(tag_id=tag.id, user=user)

    yield tagbookmark


@pytest.fixture(scope="function")
def bookmarks(user, tagbookmark):

    bookmark1 = Bookmark.objects.create(
        id=1,
        title="Bookmark 1",
        url="http://www.bordercore.com",
        user=user
    )
    bookmark2 = Bookmark.objects.create(
        id=2,
        title="Bookmark 2",
        url="http://www.bordercore.com",
        user=user
    )
    bookmark3 = Bookmark.objects.create(
        id=3,
        title="Bookmark 3",
        url="http://www.bordercore.com",
        user=user
    )

    TagBookmarkSortOrder.objects.create(tag_bookmark=tagbookmark, bookmark=bookmark3)
    TagBookmarkSortOrder.objects.create(tag_bookmark=tagbookmark, bookmark=bookmark2)
    TagBookmarkSortOrder.objects.create(tag_bookmark=tagbookmark, bookmark=bookmark1)

    yield [bookmark1, bookmark2, bookmark3]
