from urllib.parse import quote_plus

import django

django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob  # isort:skip


def test_get_s3_key_from_uuid(blob_image_factory):
    s3_key = Blob.get_s3_key_from_uuid(blob_image_factory.uuid, blob_image_factory.file)
    assert s3_key == f"blobs/{blob_image_factory.uuid}/{blob_image_factory.file}"


def test_get_edition_string(blob_image_factory):

    assert blob_image_factory.get_edition_string() == "Second Edition"

    blob_image_factory.name = "Name"
    assert blob_image_factory.get_edition_string() == ""


def test_doctype(blob_image_factory, blob_text_factory):

    assert blob_image_factory.doctype == "image"
    assert blob_text_factory.doctype == "document"


def test_get_metadata(blob_image_factory):

    metadata, urls = blob_image_factory.get_metadata()
    assert "John Smith" in [value for key, value in metadata.items()]
    assert urls[0]["domain"] == "www.bordercore.com"
    assert urls[0]["url"] == "https://www.bordercore.com"


def test_get_content_type():
    assert Blob.get_content_type("application/octet-stream") == "Video"
    assert Blob.get_content_type("text/css") == ""


def test_get_parent_dir(blob_image_factory):
    parent_dir = blob_image_factory.get_parent_dir()
    assert parent_dir == f"blobs/{blob_image_factory.uuid}"


def test_get_url(blob_image_factory):
    url = blob_image_factory.get_url()
    assert url == f"{blob_image_factory.uuid}/{quote_plus(str(blob_image_factory.file))}"


def test_get_name(blob_image_factory):

    assert blob_image_factory.get_name() == "Vaporwave Wallpaper 2E"
    assert blob_image_factory.get_name(remove_edition_string=True) == "Vaporwave Wallpaper"

    blob_image_factory.name = ""
    assert blob_image_factory.get_name(use_filename_if_present=True) == blob_image_factory.file
    assert blob_image_factory.get_name() == "No name"


def test_get_tags(blob_image_factory):
    assert blob_image_factory.get_tags() == "django, linux, video"


def test_get_collection_info(collection, blob_pdf_factory):
    assert len(blob_pdf_factory.get_collection_info()) == 1
    assert blob_pdf_factory.get_collection_info().first().name == "collection_0"


def test_get_linked_blobs(blob_pdf_factory):
    assert len(blob_pdf_factory.get_linked_blobs()) == 0


def test_get_date(blob_image_factory):
    assert blob_image_factory.get_date() == "March 04, 2021"


def test_has_thumbnail_url(blob_image_factory):
    assert blob_image_factory.has_thumbnail_url() is False


def test_is_ingestible_file(blob_image_factory):
    assert Blob.is_ingestible_file("file.png") is False
    assert Blob.is_ingestible_file("file.pdf") is True


def test_get_cover_info(blob_image_factory, blob_pdf_factory):

    cover_info = blob_image_factory.get_cover_info()
    assert cover_info["height"] == 1689
    assert cover_info["width"] == 1600

    cover_info = blob_image_factory.get_cover_info(size="small")
    assert cover_info["url"] == f"https://blobs.bordercore.com/{blob_image_factory.uuid}/cover.jpg"

    cover_info_pdf = blob_pdf_factory.get_cover_info()
    assert cover_info_pdf["url"] == f"https://blobs.bordercore.com/{blob_pdf_factory.uuid}/cover-large.jpg"

    cover_info_pdf = blob_pdf_factory.get_cover_info(size="small")
    assert cover_info_pdf["url"] == f"https://blobs.bordercore.com/{blob_pdf_factory.uuid}/cover.jpg"

    assert Blob.get_cover_info_static(blob_pdf_factory.user, None) == {"url": ""}


def count_nodes(nodes, root_node=True):

    return (0 if root_node else 1) + sum(count_nodes(node["nodes"], False) for node in nodes)


def test_parse_nodes(blob_text_factory):

    blob_text_factory.content = ""
    tree = blob_text_factory.get_tree()
    assert count_nodes(tree) == 0

    blob_text_factory.content = """
    # Node 1
    """
    tree = blob_text_factory.get_tree()
    assert count_nodes(tree) == 1
    assert tree[0]["id"] == 1
    assert tree[0]["label"] == "Node 1"
    assert tree[0]["nodes"] == []

    blob_text_factory.content = """
    ### Node 1
    Content
    #### Subnode 1a
    Content
    ### Node 2
    """

    tree = blob_text_factory.get_tree()
    assert count_nodes(tree) == 3
    assert tree[0]["id"] == 1
    assert tree[0]["label"] == "Node 1"
    assert tree[0]["nodes"][0]["id"] == 2
    assert tree[0]["nodes"][0]["label"] == "Subnode 1a"
    assert tree[0]["nodes"][0]["nodes"] == []
    assert tree[1]["id"] == 3
    assert tree[1]["label"] == "Node 2"
    assert tree[1]["nodes"] == []

    blob_text_factory.content = """
    ## Node 1
    ### Subnode 1a
    ### Subnode 1b
    ### Subnode 1c
    ### Subnode 1d
    ## Node 2
    ## Node 3
    ### Subnode 3a
    """

    tree = blob_text_factory.get_tree()
    assert count_nodes(tree) == 8
    assert tree[0]["id"] == 1
    assert tree[0]["label"] == "Node 1"
    assert tree[0]["nodes"][0]["id"] == 2
    assert tree[0]["nodes"][0]["label"] == "Subnode 1a"
    assert tree[0]["nodes"][0]["nodes"] == []
    assert tree[0]["nodes"][1]["id"] == 3
    assert tree[0]["nodes"][1]["label"] == "Subnode 1b"
    assert tree[0]["nodes"][1]["nodes"] == []
    assert tree[0]["nodes"][2]["id"] == 4
    assert tree[0]["nodes"][2]["label"] == "Subnode 1c"
    assert tree[0]["nodes"][2]["nodes"] == []
    assert tree[0]["nodes"][3]["id"] == 5
    assert tree[0]["nodes"][3]["label"] == "Subnode 1d"
    assert tree[0]["nodes"][3]["nodes"] == []
    assert tree[1]["id"] == 6
    assert tree[1]["label"] == "Node 2"
    assert tree[1]["nodes"] == []
    assert tree[2]["id"] == 7
    assert tree[2]["label"] == "Node 3"
    assert tree[2]["nodes"][0]["id"] == 8
    assert tree[2]["nodes"][0]["label"] == "Subnode 3a"
    assert tree[2]["nodes"][0]["nodes"] == []
