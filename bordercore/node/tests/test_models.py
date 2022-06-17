import pytest

import django

from blob.models import Blob
from collection.models import Collection

django.setup()


pytestmark = pytest.mark.django_db


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


def test_add_note(monkeypatch_blob, node):

    note = node.add_note()

    # Verify that the note has been added to the node's layout
    assert str(note.uuid) in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_delete_note(node):

    note = node.add_collection()
    node.delete_collection(note.uuid)

    assert Blob.objects.filter(uuid=note.uuid).first() is None

    # Verify that the collection has been removed from the node's layout
    assert str(note.uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_populate_names(node):

    collection_1 = node.add_collection()
    collection_2 = node.add_collection()
    collection_3 = node.add_collection()

    node.populate_names()

    names = [
        val["name"]
        for sublist in node.layout
        for val in sublist
        if "name" in val
    ]

    assert collection_1.name in names
    assert collection_2.name in names
    assert collection_3.name in names


def test_set_note_color(monkeypatch_blob, node):

    note = node.add_note()
    color = 1
    node.set_note_color(note.uuid, color)

    assert color in [
        val["color"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
        and val["uuid"] == str(note.uuid)
    ]
