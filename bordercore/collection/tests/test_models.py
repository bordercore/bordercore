import pytest

from collection.models import SortOrderCollectionBlob

pytestmark = pytest.mark.django_db


def test_sort_collection(collection, blob_image_factory, blob_pdf_factory):

    # Move the first blob to the second position
    so = SortOrderCollectionBlob.objects.get(collection=collection, blob=blob_pdf_factory)
    SortOrderCollectionBlob.reorder(so, 2)
    so = SortOrderCollectionBlob.objects.filter(collection=collection)
    assert so[0].blob.id == 1000
    assert so[1].blob.id == 2000
    assert collection.blobs.count() == 2

    # Move it back the first position
    so = SortOrderCollectionBlob.objects.get(collection=collection, blob=blob_pdf_factory)
    SortOrderCollectionBlob.reorder(so, 1)
    so = SortOrderCollectionBlob.objects.filter(collection=collection)
    assert so[0].blob.id == 2000
    assert so[1].blob.id == 1000
    assert collection.blobs.count() == 2

    # Move the second blob to the first position
    so = SortOrderCollectionBlob.objects.get(collection=collection, blob=blob_image_factory)
    SortOrderCollectionBlob.reorder(so, 1)
    so = SortOrderCollectionBlob.objects.filter(collection=collection)
    assert so[0].blob.id == 1000
    assert so[1].blob.id == 2000
    assert collection.blobs.count() == 2


def test_get_tags(collection):

    # Use set() since get_tags() doesn't guarantee sort order
    assert set([x.strip() for x in collection.get_tags().split(",")]) == set(["django", "linux"])


def test_get_blob(collection):

    assert collection.get_blob(-1) == {}
    assert collection.get_blob(0)["blob_id"] == 2000
    assert collection.get_blob(1)["blob_id"] == 1000
    assert collection.get_blob(3) == {}
