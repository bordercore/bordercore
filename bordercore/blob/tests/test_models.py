import datetime
import time
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import boto3
from faker import Factory as FakerFactory

import django
from django.conf import settings

from collection.models import Collection

django.setup()

from blob.models import Blob  # isort:skip
from blob.tests.factories import BlobFactory

faker = FakerFactory.create()


def test_get_s3_key(blob_image_factory, blob_text_factory):
    s3_key = Blob.get_s3_key(blob_image_factory[0].uuid, blob_image_factory[0].file)
    assert s3_key == f"blobs/{blob_image_factory[0].uuid}/{blob_image_factory[0].file}"

    assert blob_image_factory[0].s3_key == f"blobs/{blob_image_factory[0].uuid}/{blob_image_factory[0].file}"

    assert blob_text_factory[0].s3_key is None


def test_get_doctype(blob_image_factory, blob_note, blob_text_factory):

    assert blob_image_factory[0].doctype == "image"
    assert blob_note[0].doctype == "note"
    assert blob_text_factory[0].doctype == "document"


def test_get_edition_string(blob_image_factory):

    blob_image_factory[0].name = "Introduction to Electrodynamics 4E"
    assert blob_image_factory[0].get_edition_string() == "Fourth Edition"

    blob_image_factory[0].name = "Name"
    assert blob_image_factory[0].get_edition_string() == ""


def test_doctype(blob_image_factory, blob_text_factory):

    blob_image_factory[0].file = "foo.jpg"
    assert blob_image_factory[0].doctype == "image"

    blob_image_factory[0].file = "foo.pdf"
    assert blob_text_factory[0].doctype == "document"


def test_get_metadata(blob_image_factory):

    metadata, urls = blob_image_factory[0].get_metadata()
    assert blob_image_factory[0].metadata.first().value in [value for key, value in metadata.items()]

    url = blob_image_factory[0].metadata.filter(name="Url").first()
    assert urls[0]["url"] == url.value
    assert urls[0]["domain"] == urlparse(url.value).netloc


def test_has_been_modified(auto_login_user, blob_image_factory):

    user, _ = auto_login_user()

    blob = BlobFactory.create(user=user)
    assert blob.has_been_modified() is False

    blob.name = faker.text(max_nb_chars=10)

    # The resolution of has_been_modified() is one second, so
    #  we need to wait at least that long to see a difference.
    time.sleep(1)

    blob.save()
    assert blob.has_been_modified() is True


def test_get_content_type():
    assert Blob.get_content_type("application/octet-stream") == "Video"
    assert Blob.get_content_type("text/css") == ""


def test_get_parent_dir(blob_image_factory):
    parent_dir = blob_image_factory[0].get_parent_dir()
    assert parent_dir == f"blobs/{blob_image_factory[0].uuid}"


def test_get_url(blob_image_factory):
    url = blob_image_factory[0].get_url()
    assert url == f"{blob_image_factory[0].uuid}/{quote_plus(str(blob_image_factory[0].file))}"


def test_get_name(blob_image_factory):

    blob_image_factory[0].name = "Vaporwave Wallpaper 2E"
    assert blob_image_factory[0].get_name() == "Vaporwave Wallpaper 2E"
    assert blob_image_factory[0].get_name(remove_edition_string=True) == "Vaporwave Wallpaper"

    blob_image_factory[0].name = ""
    assert blob_image_factory[0].get_name(use_filename_if_present=True) == blob_image_factory[0].file
    assert blob_image_factory[0].get_name() == "No name"


def test_get_tags(blob_image_factory):
    assert blob_image_factory[0].get_tags() == "django, linux, video"


def test_is_pinned_note(blob_note):
    assert blob_note[0].is_pinned_note() is False


def test_get_collection_info(collection, blob_pdf_factory):
    assert len(blob_pdf_factory[0].get_collection_info()) == 2
    assert blob_pdf_factory[0].get_collection_info().first().name == "To Display"


def test_get_linked_blobs(blob_pdf_factory):
    assert len(blob_pdf_factory[0].get_linked_objects()) == 0


def test_get_date(blob_image_factory):
    assert blob_image_factory[0].get_date() == datetime.datetime.strptime(blob_image_factory[0].date, '%Y-%m-%d').strftime('%B %d, %Y')


def test_is_ingestible_file(blob_image_factory):
    assert Blob.is_ingestible_file("file.png") is False
    assert Blob.is_ingestible_file("file.pdf") is True


def test_duration_humanized():
    assert Blob.get_duration_humanized(8.356) == "0:08"
    assert Blob.get_duration_humanized(18.356) == "0:18"
    assert Blob.get_duration_humanized(218.356) == "3:38"
    assert Blob.get_duration_humanized(918.356) == "15:18"
    assert Blob.get_duration_humanized(6918.356) == "1:55:18"


def test_clone(temp_blob_directory, monkeypatch_blob, blob_pdf_factory, collection):

    cloned_blob = blob_pdf_factory[0].clone()
    assert cloned_blob.date == blob_pdf_factory[0].date
    assert cloned_blob.tags.all().count() == blob_pdf_factory[0].tags.all().count()
    assert cloned_blob.metadata.all().count() == blob_pdf_factory[0].metadata.all().count()

    for metadata in blob_pdf_factory[0].metadata.all():
        assert metadata.name in [x.name for x in cloned_blob.metadata.all()]

    for tag in blob_pdf_factory[0].tags.all():
        assert tag in cloned_blob.tags.all()

    for c in Collection.objects.filter(collectionobject__blob__uuid=blob_pdf_factory[0].uuid):
        assert cloned_blob in [x.blob for x in c.collectionobject_set.all()]


def test_blob_update_cover_image(blob_pdf_factory, s3_resource, s3_bucket):

    file_path = Path(__file__).parent / "resources/cover-large.jpg"

    with open(file_path, "rb") as fh:
        image = fh.read()

    blob_pdf_factory[0].update_cover_image(image)

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    objects = [
        x.key
        for x in list(bucket.objects.filter(Prefix=f"blobs/{blob_pdf_factory[0].uuid}/"))
    ]

    # There should be 3 objects. The original blob plus the two cover images
    assert len(objects) == 3
    assert f"blobs/{blob_pdf_factory[0].uuid}/cover.jpg" in objects
    assert f"blobs/{blob_pdf_factory[0].uuid}/cover-large.jpg" in objects


def test_blob_rename_file(blob_pdf_factory):

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    filename = faker.file_name(extension="pdf")
    blob_pdf_factory[0].rename_file(filename)

    # Verify that the blob's new filename has been changed in S3
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key_root = f"{settings.MEDIA_ROOT}/{blob_pdf_factory[0].uuid}"
    objects = [
        x.key
        for x in list(bucket.objects.filter(Prefix=f"{key_root}/"))
    ]
    assert len(objects) == 1
    assert f"{key_root}/{filename}" in objects


def count_nodes(nodes, root_node=True):

    return (0 if root_node else 1) + sum(count_nodes(node["nodes"], False) for node in nodes)


def test_parse_nodes(blob_text_factory):

    blob_text_factory[0].content = ""
    tree = blob_text_factory[0].get_tree()
    assert count_nodes(tree) == 0

    blob_text_factory[0].content = """
    # Node 1
    """
    tree = blob_text_factory[0].get_tree()
    assert count_nodes(tree) == 1
    assert tree[0]["id"] == 1
    assert tree[0]["label"] == "Node 1"
    assert tree[0]["nodes"] == []

    blob_text_factory[0].content = """
    ### Node 1
    Content
    #### Subnode 1a
    Content
    ### Node 2
    """

    tree = blob_text_factory[0].get_tree()
    assert count_nodes(tree) == 3
    assert tree[0]["id"] == 1
    assert tree[0]["label"] == "Node 1"
    assert tree[0]["nodes"][0]["id"] == 2
    assert tree[0]["nodes"][0]["label"] == "Subnode 1a"
    assert tree[0]["nodes"][0]["nodes"] == []
    assert tree[1]["id"] == 3
    assert tree[1]["label"] == "Node 2"
    assert tree[1]["nodes"] == []

    blob_text_factory[0].content = """
    ## Node 1
    ### Subnode 1a
    ### Subnode 1b
    ### Subnode 1c
    ### Subnode 1d
    ## Node 2
    ## Node 3
    ### Subnode 3a
    """

    tree = blob_text_factory[0].get_tree()
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
