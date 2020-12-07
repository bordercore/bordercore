
import pytest

import django

django.setup()

from bookmark.models import Bookmark  # isort:skip
from tag.models import Tag, SortOrderTagBookmark  # isort:skip


@pytest.fixture(scope="function")
def tag(user):

    tag1 = Tag.objects.create(name="django")

    tag2 = Tag.objects.create(name="video", is_meta=True)

    yield [tag1, tag2]


@pytest.fixture(scope="function")
def bookmarks(user, tag):

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

    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark3)
    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark2)
    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark1)

    yield [bookmark1, bookmark2, bookmark3]
