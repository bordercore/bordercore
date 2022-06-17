import json

import pytest
from faker import Factory as FakerFactory

from django import urls

from blob.models import Blob
from collection.models import Collection
from node.models import Node

pytestmark = [pytest.mark.django_db, pytest.mark.views]


faker = FakerFactory.create()


def test_node_listview(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_node_detail(auto_login_user, node, blob_image_factory, blob_pdf_factory):

    _, client = auto_login_user()

    url = urls.reverse("node:detail", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_node_create(auto_login_user, node):

    _, client = auto_login_user()

    node_name = faker.text(max_nb_chars=32)

    url = urls.reverse("node:create")
    resp = client.post(url, {
        "name": node_name,
        "note": faker.text(max_nb_chars=100)
    })

    assert resp.status_code == 302
    assert Node.objects.filter(name=node_name).exists()


def test_edit_note(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:edit_note")
    resp = client.post(url, {
        "uuid": node.uuid,
        "note": "Sample Changed Note"
    })

    assert resp.status_code == 200


def test_change_layout(auto_login_user, node):

    _, client = auto_login_user()

    layout = [[{"type": "note"}], [{"type": "bookmark"}], [{"type": "blob"}]]

    url = urls.reverse("node:change_layout")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "layout": json.dumps(layout)
    })

    assert resp.status_code == 200

    changed_node = Node.objects.get(uuid=node.uuid)
    assert changed_node.layout == layout


def test_add_collection(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:add_collection")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "collection_name": "Test Collection",
    })

    assert resp.status_code == 200

    resp_json = resp.json()
    updated_node = Node.objects.get(uuid=node.uuid)
    # Verify that the collection has been added to the node's layout
    assert resp_json["collection_uuid"] in [
        val["uuid"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_delete_collection(auto_login_user, node):

    _, client = auto_login_user()

    collection = node.add_collection()

    url = urls.reverse("node:delete_collection")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "collection_uuid": collection.uuid
    })

    assert resp.status_code == 200

    assert Collection.objects.filter(uuid=collection.uuid).first() is None

    # Verify that the collection has been removed from the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)
    assert collection.uuid not in [
        val["uuid"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_add_note(monkeypatch_blob, auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:add_note")
    resp = client.post(url, {
        "node_uuid": node.uuid,
    })

    assert resp.status_code == 200

    resp_json = resp.json()
    updated_node = Node.objects.get(uuid=node.uuid)
    # Verify that the note has been added to the node's layout
    assert resp_json["note_uuid"] in [
        val["uuid"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_delete_note(monkeypatch_blob, auto_login_user, node):

    _, client = auto_login_user()

    note = node.add_note()

    url = urls.reverse("node:delete_note")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "note_uuid": note.uuid
    })

    assert resp.status_code == 200

    assert Blob.objects.filter(uuid=note.uuid).first() is None

    # Verify that the collection has been removed from the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)
    assert note.uuid not in [
        val["uuid"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val
    ]


def test_node_set_note_color(monkeypatch_blob, auto_login_user, node):

    _, client = auto_login_user()

    note = node.add_note()
    color = 2

    url = urls.reverse("node:set_note_color")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "note_uuid": note.uuid,
        "color": color
    })

    assert resp.status_code == 200

    # Verify that the collection has been removed from the node's layout
    updated_node = Node.objects.get(uuid=node.uuid)

    assert color in [
        val["color"]
        for sublist in updated_node.layout
        for val in sublist
        if "uuid" in val
        and val["uuid"] == str(note.uuid)
    ]
