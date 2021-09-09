import pytest

from collection.models import SortOrderCollectionBlob

pytestmark = pytest.mark.django_db


def test_sort_collection(collection, blob_image_factory, blob_pdf_factory):

    # Move the first blob to the second position
    so = SortOrderCollectionBlob.objects.get(collection=collection[0], blob=blob_pdf_factory)
    SortOrderCollectionBlob.reorder(so, 2)
    so = SortOrderCollectionBlob.objects.filter(collection=collection[0])
    assert so[0].blob.id == 1000
    assert so[1].blob.id == 2000
    assert collection[0].blobs.count() == 2

    # Move it back the first position
    so = SortOrderCollectionBlob.objects.get(collection=collection[0], blob=blob_pdf_factory)
    SortOrderCollectionBlob.reorder(so, 1)
    so = SortOrderCollectionBlob.objects.filter(collection=collection[0])
    assert so[0].blob.id == 2000
    assert so[1].blob.id == 1000
    assert collection[0].blobs.count() == 2

    # Move the second blob to the first position
    so = SortOrderCollectionBlob.objects.get(collection=collection[0], blob=blob_image_factory)
    SortOrderCollectionBlob.reorder(so, 1)
    so = SortOrderCollectionBlob.objects.filter(collection=collection[0])
    assert so[0].blob.id == 1000
    assert so[1].blob.id == 2000
    assert collection[0].blobs.count() == 2


def test_get_tags(collection):

    # Use set() since get_tags() doesn't guarantee sort order
    assert set([x.strip() for x in collection[0].get_tags().split(",")]) == set(["django", "linux"])


def test_get_blob(collection):

    assert collection[0].get_blob(-1) == {}
    assert collection[0].get_blob(3) == {}


def test_get_blob_list(collection, blob_image_factory, blob_pdf_factory):

    blob_list = collection[0].get_blob_list()

    assert len(blob_list) == 2
    assert str(blob_list[0]["uuid"]) == blob_pdf_factory.uuid
    assert str(blob_list[1]["uuid"]) == blob_image_factory.uuid
    assert blob_list[0]["name"] == blob_pdf_factory.name
    assert blob_list[1]["name"] == blob_image_factory.name
