import io
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import boto3
import factory
import pytest
from faker import Factory as FakerFactory
from PIL import Image

from django import urls
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import signals

from blob.models import Blob, BlobToObject
from blob.tests.factories import BlobFactory
from blob.views import handle_linked_collection, handle_metadata
from collection.models import Collection
from collection.tests.factories import CollectionFactory

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = [pytest.mark.django_db, pytest.mark.views]

faker = FakerFactory.create()


def mock(*args, **kwargs):
    pass


@pytest.fixture
def monkeypatch_collection(monkeypatch):
    """
    Prevent the collection object from interacting with AWS by
    patching out a method.
    """

    monkeypatch.setattr(Collection, "create_collection_thumbnail", mock)


def test_blob_list(auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_blob_create(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:create")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("blob:create")
    resp = client.post(url, {
        "tags": "django",
        "importance": 1,
    })

    assert resp.status_code == 200

    # A blob linked to an existing blob -- empty form
    url = urls.reverse("blob:create")
    resp = client.get(url, {
        "tags": "django",
        "importance": 1,
        "linked_blob_uuid": blob_text_factory[0].uuid
    })

    assert resp.status_code == 200

    # A blob linked to an existing blob -- submitted form
    url = urls.reverse("blob:create")
    resp = client.post(url, {
        "tags": "django",
        "importance": 1,
        "linked_blob_uuid": blob_text_factory[0].uuid
    })

    assert resp.status_code == 200

    new_blob = Blob.objects.all().order_by("-created")[0]
    assert BlobToObject.objects.get(node=blob_text_factory[0], blob=new_blob).blob.uuid == new_blob.uuid

    # A new blob with a file
    file_path = Path(__file__).parent / "resources/test_blob.jpg"
    with open(file_path, "rb") as f:
        file_blob = f.read()
    file_upload = SimpleUploadedFile(file_path.name, file_blob)
    name = faker.text(max_nb_chars=10)
    url = urls.reverse("blob:create")
    resp = client.post(url, {
        "importance": 1,
        "file": file_upload,
        "filename": file_path.name,
        "name": name,
        "tags": "django",
    })

    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "OK"
    blob_uuid = json.loads(resp.content)["uuid"]
    blob = Blob.objects.get(uuid=blob_uuid)
    assert blob.name == name

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key_root = f"{settings.MEDIA_ROOT}/{blob.uuid}"

    # Verify that the blob's file is in S3
    objects = [
        x.key
        for x in list(bucket.objects.filter(Prefix=f"{key_root}/"))
    ]
    assert len(objects) == 1
    assert f"{key_root}/{file_path.name}" in objects


@factory.django.mute_signals(signals.pre_delete)
def test_blob_delete(monkeypatch_blob, auto_login_user, blob_text_factory):

    # Quiet spurious output
    settings.NPLUSONE_WHITELIST = [
        {
            "label": "unused_eager_load",
            "model": "blob.Blob"
        }
    ]

    _, client = auto_login_user()
    url = urls.reverse("blob-detail", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.delete(url)

    assert resp.status_code == 204
    assert not Blob.objects.filter(uuid=blob_text_factory[0].uuid).exists()


@factory.django.mute_signals(signals.post_save)
def test_blob_update(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    # The empty form
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200

    # The submitted form
    file_path = Path(__file__).parent / "resources/test_blob.pdf"
    with open(file_path, "rb") as f:
        file_blob = f.read()
    file_upload = SimpleUploadedFile(file_path.name, file_blob)
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.post(url, {
        "file": file_upload,
        "filename": file_path.name,
        "importance": 1,
        "name": "Name Changed",
        "note": "Note Changed",
        "tags": "django"
    })
    assert resp.status_code == 200

    # Test a blob's file is changed
    file_path = Path(__file__).parent / "resources/test_blob.jpg"
    with open(file_path, "rb") as f:
        file_blob = f.read()
    file_upload = SimpleUploadedFile(file_path.name, file_blob)
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.post(url, {
        "file": file_upload,
        "filename": file_path.name,
        "importance": 1,
        "name": "Name Changed",
        "note": "Note Changed",
        "tags": "django"
    })

    assert resp.status_code == 200

    # Verify that the blob's new file is in S3
    key_root = f"{settings.MEDIA_ROOT}/{blob_text_factory[0].uuid}"
    objects = [
        x.key
        for x in list(bucket.objects.filter(Prefix=f"{key_root}/"))
    ]
    assert len(objects) == 1
    assert f"{key_root}/{file_path.name}" in objects

    # Test a blob's filename is changed
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    filename_new = faker.file_name(extension="jpg")
    resp = client.post(url, {
        "filename": filename_new,
        "tags": ""
    })
    assert resp.status_code == 200

    # Verify that the blob's new filename has been changed in S3
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key_root = f"{settings.MEDIA_ROOT}/{blob_text_factory[0].uuid}"
    objects = [
        x.key
        for x in list(bucket.objects.filter(Prefix=f"{key_root}/"))
    ]
    assert len(objects) == 1
    assert f"{key_root}/{filename_new}" in objects


@pytest.mark.parametrize("blob", [pytest.lazy_fixture("blob_image_factory"), pytest.lazy_fixture("blob_text_factory")])
def test_blob_detail(auto_login_user, blob):

    _, client = auto_login_user()

    url = urls.reverse("blob:detail", args=(blob[0].uuid,))
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    assert soup.select("div#vue-app #blob-name")[0].findAll(text=True)[0].strip() == blob[0].get_name(remove_edition_string=True)

    url = [x.value for x in blob[0].metadata.all() if x.name == "Url"][0]
    assert soup.select("strong a")[0].findAll(text=True)[0] == urlparse(url).netloc

    author = [x.value for x in blob[0].metadata.all() if x.name == "Author"][0]
    assert author in [x for sublist in soup.select("span") for x in sublist]


def test_clone(monkeypatch_blob, auto_login_user):

    user, client = auto_login_user()

    blob = BlobFactory.create(user=user)

    url = urls.reverse("blob:clone", kwargs={"uuid": str(blob.uuid)})
    resp = client.get(url)

    assert resp.status_code == 302


def test_handle_metadata(auto_login_user, blob_text_factory, blob_image_factory):

    user, client = auto_login_user()

    request_mock = Mock()
    request_mock.user = user
    fake_name = faker.name()
    fake_url = faker.url()

    request_mock.POST = {
        "metadata": json.dumps(
            [
                {"name": "Artist", "value": fake_name},
                {"name": "Url", "value": fake_url}
            ]
        )
    }

    handle_metadata(blob_text_factory[0], request_mock)

    metadata = blob_text_factory[0].metadata.all()
    assert len(metadata) == 2
    assert "Artist" in [x.name for x in metadata]
    assert fake_name in [x.value for x in metadata]
    assert "Url" in [x.name for x in metadata]
    assert fake_url in [x.value for x in metadata]

    request_mock.POST = {
        "metadata": json.dumps(
            [
                {"name": "Author", "value": fake_name},
                {"name": "is_book", "value": "true"}
            ]
        )
    }

    handle_metadata(blob_image_factory[0], request_mock)

    metadata = blob_image_factory[0].metadata.all()
    assert len(metadata) == 2
    assert "Author" in [x.name for x in metadata]
    assert fake_name in [x.value for x in metadata]
    assert "is_book" in [x.name for x in metadata]


def test_handle_linked_collection(monkeypatch_collection, auto_login_user, blob_image_factory):

    user, client = auto_login_user()

    collection = CollectionFactory(user=user)

    request_mock = Mock()
    request_mock.user = user
    request_mock.POST = {
        "linked_collection": collection.uuid
    }

    handle_linked_collection(blob_image_factory[0], request_mock)

    collection_updated = Collection.objects.get(uuid=collection.uuid)

    assert blob_image_factory[0] in [x.blob for x in collection_updated.collectionobject_set.all()]


def test_blob_metadata_name_search(auto_login_user, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob:metadata_name_search")
    resp = client.get(f"{url}?query=foobar")

    assert resp.status_code == 200


def test_blob_parse_date(auto_login_user):

    _, client = auto_login_user()

    url = urls.reverse("blob:parse_date", kwargs={"input_date": "2021-01-01"})
    resp = client.get(url)
    assert resp.json() == {'output_date': '2021-01-01T00:00', 'error': None}
    assert resp.status_code == 200

    # Test a bogus date
    url = urls.reverse("blob:parse_date", kwargs={"input_date": "2021-01-34"})
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.json() == {'output_date': '', 'error': "time data '01/34/2021' does not match format '%m/%d/%Y'"}


def test_blob_update_cover_image(s3_resource, s3_bucket, auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)

    file_path = Path(__file__).parent / "resources/test_blob.jpg"
    img = Image.open(file_path)
    imgByteArr = io.BytesIO()
    img.save(imgByteArr, "jpeg")
    image_upload = SimpleUploadedFile(file_path.name, imgByteArr.getvalue())

    url = urls.reverse("blob:update_cover_image")
    resp = client.post(url, {
        "blob_uuid": blob_1.uuid,
        "image": image_upload,
    })

    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "OK"


def test_get_elasticsearch_info(auto_login_user):

    user, client = auto_login_user()

    blob = BlobFactory.create(user=user, tags=("django", "linux"),)

    url = urls.reverse("blob:get_elasticsearch_info", kwargs={"uuid": blob.uuid})
    resp = client.get(url)

    assert resp.status_code == 200
    assert resp.json() == {"info": {}, "status": "OK"}

    BlobFactory.index_blob(blob)

    # Pause to allow time for the blob to be indexed
    time.sleep(1)

    url = urls.reverse("blob:get_elasticsearch_info", kwargs={"uuid": blob.uuid})
    resp_json = client.get(url).json()

    assert resp.status_code == 200
    assert resp_json["status"] == "OK"
    assert resp_json["info"]["id"] == str(blob.uuid)
    assert resp_json["info"]["name"] == blob.name
    assert resp_json["info"]["filename"] == ""
    assert resp_json["info"]["note"] == blob.note
    assert resp_json["info"]["doctype"] == "document"


def test_related_objects(auto_login_user):

    # Quiet spurious output
    settings.NPLUSONE_WHITELIST = [
        {
            "label": "unused_eager_load",
            "model": "blob.BlobToObject"
        }
    ]

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    BlobToObject.objects.create(node=blob_1, blob=blob_2)

    url = urls.reverse("blob:related_objects", kwargs={"uuid": str(blob_1.uuid)})
    resp = client.get(url)

    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "OK"
    assert len(payload["blob_list"]) == 1
    assert payload["blob_list"][0]["uuid"] == str(blob_2.uuid)


def test_blob_add_related_object(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    url = urls.reverse("blob:add_related_object")
    resp = client.post(url, {
        "node_uuid": blob_1.uuid,
        "object_uuid": blob_2.uuid,
    })

    assert resp.status_code == 200

    related_blobs = BlobToObject.objects.filter(node=blob_1)
    assert related_blobs.count() == 1
    assert related_blobs.first().blob == blob_2


def test_blob_remove_related_object(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    BlobToObject.objects.create(node=blob_1, blob=blob_2)

    url = urls.reverse("blob:remove_related_object")
    resp = client.post(url, {
        "node_uuid": blob_1.uuid,
        "object_uuid": blob_2.uuid,
    })

    assert resp.status_code == 200

    related_blobs = BlobToObject.objects.filter(node=blob_1)
    assert related_blobs.count() == 0


def test_blob_update_page_number(auto_login_user):

    user, client = auto_login_user()

    blob = BlobFactory.create(user=user)
    page_number = 2

    url = urls.reverse("blob:update_page_number")

    # Patch out the call to invoke the AWS lambda to update
    #  the blob's thumbnail
    with patch("botocore.client.BaseClient._make_api_call", new=mock):

        resp = client.post(url, {
            "blob_uuid": blob.uuid,
            "page_number": page_number
        })

        assert resp.status_code == 200

    blob_updated = Blob.objects.get(uuid=blob.uuid)
    assert blob_updated.data == {"pdf_page_number": page_number}


def test_blob_update_related_object_note(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    BlobToObject.objects.create(node=blob_1, blob=blob_2)

    note = faker.text()

    url = urls.reverse("blob:update_related_object_note")
    resp = client.post(url, {
        "node_uuid": blob_1.uuid,
        "object_uuid": blob_2.uuid,
        "note": note
    })

    assert resp.status_code == 200

    related_object = BlobToObject.objects.get(node=blob_1, blob=blob_2)
    assert related_object.note == note
