import json

import pytest

import django

from blob.models import Blob
from collection.models import Collection
from node.models import Node
from quote.tests.factories import QuoteFactory

django.setup()


pytestmark = pytest.mark.django_db


def test_node_add_collection(node):

    collection = node.add_collection()

    # Verify that the collection has been added to the node's layout
    assert str(collection.uuid) in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_node_update_collection(node):

    collection = node.add_collection()
    display = "individual"
    rotate = "rotate"

    node.update_collection(str(collection.uuid), display, rotate)

    # Verify that the collection's properties have been updated in the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)

    assert display in [
        val["display"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val and val["uuid"] == str(collection.uuid)
    ]
    assert rotate in [
        val["rotate"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val and val["uuid"] == str(collection.uuid)
    ]


def test_node_delete_collection(node):

    collection = node.add_collection()
    node.delete_collection(collection.uuid, "ad-hoc")

    assert Collection.objects.filter(uuid=collection.uuid).first() is None

    # Verify that the collection has been removed from the node's layout
    assert str(collection.uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_node_add_note(monkeypatch_blob, node):

    note = node.add_note()

    # Verify that the note has been added to the node's layout
    assert str(note.uuid) in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_node_delete_note(monkeypatch_blob, node):

    note = node.add_note()
    node.delete_note(note.uuid)

    assert Blob.objects.filter(uuid=note.uuid).first() is None

    # Verify that the note has been removed from the node's layout
    assert str(note.uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_get_layout(node):

    layout = node.get_layout()

    assert "New Collection" in [
        val["name"]
        for sublist in json.loads(layout)
        for val in sublist
        if val["type"] == "collection"
    ]

    assert True


def test_node_populate_names(node):

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


def test_node_set_note_color(monkeypatch_blob, node):

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


def test_node_add_image(monkeypatch_blob, node, blob_image_factory):

    node.add_image(blob_image_factory[0].uuid)

    assert \
        {
            "uuid": str(blob_image_factory[0].uuid),
            "type": "image"
        } in [
            val
            for sublist in node.layout
            for val in sublist
            if "uuid" in val
        ]


def test_node_remove_image(node, blob_image_factory):

    node.add_image(blob_image_factory[0].uuid)

    node.remove_image(blob_image_factory[0].uuid)

    # Verify that the image has been removed from the node's layout
    assert str(blob_image_factory[0].uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_node_add_quote(node, quote):

    node_quote_uuid = node.add_quote(quote.uuid)

    # Verify that the quote has been added to the node's layout
    assert str(quote.uuid) in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "node_quote_uuid" in val
        and val["node_quote_uuid"] == node_quote_uuid
    ]


def test_node_remove_quote(node, quote):

    node_quote_uuid = node.add_quote(quote.uuid)
    node.remove_quote(node_quote_uuid)

    # Verify that the quote has been removed from the node's layout
    assert str(quote.uuid) not in [
        val["uuid"]
        for sublist in node.layout
        for val in sublist
        if "node_quote_uuid" in val
        and val["node_quote_uuid"] == node_quote_uuid
    ]


def test_node_update_quote(node, quote):

    node_quote_uuid = node.add_quote(quote.uuid)
    color = 2
    format = "standard"
    rotate = 10
    favorites_only = "false"

    node.update_quote(node_quote_uuid, color, format, rotate, favorites_only)

    # Verify that the quote's properties have been updated in the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)

    assert color in [
        val["color"]
        for sublist in updated_node.layout
        for val in sublist
        if val["type"] == "quote" and val.get("node_quote_uuid", None) == str(node_quote_uuid)
    ]
    assert rotate in [
        val["rotate"]
        for sublist in updated_node.layout
        for val in sublist
        if val["type"] == "quote" and val.get("node_quote_uuid", None) == str(node_quote_uuid)
    ]


def test_node_set_quote(auto_login_user, node):

    user, client = auto_login_user()

    quotes = QuoteFactory.create_batch(2, user=user)

    node.add_quote(quotes[0].uuid)
    node.set_quote(quotes[1].uuid)

    # Verify that the quote's properties have been updated in the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)

    assert str(quotes[1].uuid) in [
        val["uuid"]
        for sublist in updated_node.layout
        for val in sublist
        if val["type"] == "quote"
    ]
