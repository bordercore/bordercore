import pytest

import django

from collection.models import Collection

django.setup()

from node.models import SortOrderNodeBookmark, SortOrderNodeBlob  # isort:skip

pytestmark = pytest.mark.django_db


def test_reorder_bookmarks(node, bookmark):

    # Move the first bookmark down the list, from 1 -> 2
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other two bookmarks have changed their sort order
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[1])
    assert tbso.sort_order == 1

    # Move the same bookmark down the list again, from 2 -> 1
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other bookmark has changed their sort order
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[1])
    assert tbso.sort_order == 1

    # Move the same bookmark back to the top of the list
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other bookmark has changed their sort order
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[1])
    assert tbso.sort_order == 2

    # Move the last bookmark to the top of the list
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[1])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other bookmark has changed their sort order
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[0])
    assert tbso.sort_order == 2


def test_delete_bookmarks(node, bookmark):

    # Delete the first bookmark
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[0])
    tbso.delete()

    # Verify that the last bookmark has a new sort order (decrease by one)
    tbso = SortOrderNodeBookmark.objects.get(node=node, bookmark=bookmark[1])
    assert tbso.sort_order == 1


def test_reorder_blobs(node, blob_image_factory, blob_pdf_factory):

    # Move the first bookmark down the list, from 1 -> 2
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_image_factory[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other two blobs have changed their sort order
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_pdf_factory[0])
    assert tbso.sort_order == 1

    # Move the same blob down the list again, from 2 -> 1
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_image_factory[0])
    tbso.reorder(2)
    assert tbso.sort_order == 2

    # Verify that the other blob has changed their sort order
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_pdf_factory[0])
    assert tbso.sort_order == 1

    # Move the same blob back to the top of the list
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_image_factory[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other blob has changed their sort order
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_pdf_factory[0])
    assert tbso.sort_order == 2

    # Move the last blob to the top of the list
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_pdf_factory[0])
    tbso.reorder(1)
    assert tbso.sort_order == 1

    # Verify that the other blob has changed their sort order
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_image_factory[0])
    assert tbso.sort_order == 2


def test_delete_blobs(node, blob_image_factory, blob_pdf_factory):

    # Delete the first blob
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_image_factory[0])
    tbso.delete()

    # Verify that the last blob has a new sort order (decrease by one)
    tbso = SortOrderNodeBlob.objects.get(node=node, blob=blob_pdf_factory[0])
    assert tbso.sort_order == 1


def test_add_collection(node):

    collection = node.add_collection()

    # Verify that the collection has been added to the node's layout
    assert str(collection.uuid) in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_delete_collection(node):

    collection = node.add_collection()
    node.delete_collection(collection.uuid)

    assert Collection.objects.filter(uuid=collection.uuid).first() is None

    # Verify that the collection has been removed from the node's layout
    assert str(collection.uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_populate_collection_names(node):

    collection_1 = node.add_collection()
    collection_2 = node.add_collection()
    collection_3 = node.add_collection()

    node.populate_collection_names()

    names = [
        val["name"]
        for sublist in node.layout
        for val in sublist
        if "name" in val
    ]

    assert collection_1.name in names
    assert collection_2.name in names
    assert collection_3.name in names
