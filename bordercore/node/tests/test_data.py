import pytest

from blob.models import Blob
from collection.models import Collection
from node.models import Node

pytestmark = pytest.mark.data_quality


def test_node_layout_notes_exist_in_db():
    "Assert that all notes in node layouts exist in the database"
    for node in Node.objects.all():
        for i, col in enumerate(node.layout):
            for note in [x for x in col if "uuid" in x and x["type"] == "note"]:
                if not Blob.objects.filter(uuid=note["uuid"]).exists():
                    assert False, f"blob found in node layout but not in the database: node uuid={node.uuid}, note uuid={note['uuid']}"


def test_node_layout_collections_exist_in_db():
    "Assert that all collections in node layouts exist in the database"
    for node in Node.objects.all():
        for i, col in enumerate(node.layout):
            for collection in [x for x in col if "uuid" in x and x["type"] == "collection"]:
                if not Collection.objects.filter(uuid=collection["uuid"]).exists():
                    assert False, f"collection found in node layout but not in the database: node uuid={node.uuid}, collection uuid={collection['uuid']}"
