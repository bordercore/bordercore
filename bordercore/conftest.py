
import hashlib
import os
from pathlib import Path

import boto3
import botocore
import pytest
from PIL import Image

import django
from django.conf import settings
from django.core.files import File

django.setup()

from accounts.models import SortOrderUserTag  # isort:skip
from accounts.tests.factories import TEST_PASSWORD  # isort:skip
from blob.tests.factories import BlobFactory  # isort:skip
from bookmark.tests.factories import BookmarkFactory  # isort:skip
from collection.tests.factories import CollectionFactory  # isort:skip
from drill.tests.factories import QuestionFactory  # isort:skip
from tag.models import Tag  # isort:skip
from tag.models import Tag, SortOrderTagBookmark  # isort:skip
from tag.tests.factories import TagFactory  # isort:skip
from todo.tests.factories import TodoFactory, UserFactory  #isort:skip

try:
    from moto import mock_s3
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass


@pytest.fixture()
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def auto_login_user(client):

    def make_auto_login(user=None):

        if user is None:
            user = UserFactory()

        client.login(username=user.username, password=TEST_PASSWORD)
        return user, client

    return make_auto_login


@pytest.fixture()
def auto_login_user_test(client):

    print(f"cookies: {client.cookies}")

    user = UserFactory()
    result = client.login(username=user.username, password=TEST_PASSWORD)
    print(f"client a: {id(client)}, {result}")
    # print(dir(client.session))
    for x in client.session.items():
        print(x)

    print(f"cookies: {client.cookies}")

    return user, client


@pytest.fixture()
def blob_image_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        uuid="0bb4914e-cd3c-4d6b-9d72-0454adf00260",
        title="Vaporwave Wallpaper 2E",
        tags=("django", "linux", "video"),
    )

    file_path = "blob/tests/resources/test_blob.jpg"
    cover_filename = "cover.jpg"
    handle_file_info(blob, file_path, cover_filename)
    handle_s3_info_image(s3_resource, s3_bucket, blob, file_path, cover_filename)
    yield blob


@pytest.fixture()
def blob_pdf_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        uuid="4158cf58-306c-42d7-9c98-07d3a96a1d8b",
        title="Bleached Album Notes",
        tags=("django", "linux", "video"),
    )

    file_path = "blob/tests/resources/test_blob.pdf"
    cover_filename = "cover-large.jpg"
    handle_file_info(blob, file_path, cover_filename)
    handle_s3_info_pdf(s3_resource, s3_bucket, blob, file_path, cover_filename)
    yield blob


@pytest.fixture()
def bookmarks(tag):

    bookmark_1 = BookmarkFactory()
    bookmark_2 = BookmarkFactory()
    bookmark_3 = BookmarkFactory(is_pinned=True)

    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark_3)
    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark_2)
    SortOrderTagBookmark.objects.create(tag=tag[0], bookmark=bookmark_1)

    yield [bookmark_1, bookmark_2, bookmark_3]


@pytest.fixture()
def collection():

    collection = CollectionFactory()

    tag_1 = TagFactory(name="django")
    tag_2 = TagFactory(name="linux")
    collection.tags.add(tag_1, tag_2)

    yield collection


@pytest.fixture()
def question():

    question = QuestionFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    question.tags.add(tag_1)
    question.tags.add(tag_2)

    yield question


@pytest.fixture()
def s3_resource(aws_credentials):
    """Mocked S3 Fixture."""

    with mock_s3():
        yield boto3.resource(service_name="s3")


@pytest.fixture()
def s3_bucket(s3_resource):

    # Verify that the S3 mock is working
    try:
        s3_resource.meta.client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    except botocore.exceptions.ClientError:
        pass
    else:
        err = f"Bucket {settings.AWS_STORAGE_BUCKET_NAME} should not exist."
        raise EnvironmentError(err)

    s3_resource.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)


@pytest.fixture()
def sort_order_user_tag(auto_login_user):

    user, _ = auto_login_user()

    tag1, _ = Tag.objects.get_or_create(name="tag1")
    tag2, _ = Tag.objects.get_or_create(name="tag2")
    tag3, _ = Tag.objects.get_or_create(name="tag3")

    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag1)
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag2)
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag3)
    sort_order.save()


@pytest.fixture()
def tag():

    TagFactory.reset_sequence(0)

    tag_1 = TagFactory(name="django")
    tag_2 = TagFactory(name="video", is_meta=True)

    yield [tag_1, tag_2]


@pytest.fixture()
def todo_factory():

    TagFactory.reset_sequence(0)
    TodoFactory.reset_sequence(0)

    task_1 = TodoFactory(priority=1)
    task_2 = TodoFactory(priority=1)
    task_3 = TodoFactory()

    tag_1 = TagFactory()
    tag_2 = TagFactory()

    task_1.tags.add(tag_1)
    task_2.tags.add(tag_1)
    task_3.tags.add(tag_1)
    task_3.tags.add(tag_2)


def handle_file_info(blob, file_path, cover_filename):

    filepath = Path(__file__).parent / file_path
    filename = Path(filepath).name

    filepath_cover = Path(__file__).parent / f"blob/tests/resources/{cover_filename}"

    width_cover, height_cover = Image.open(filepath_cover).size

    hasher = hashlib.sha1()
    with open(filepath, "rb") as f:
        buf = f.read()
        hasher.update(buf)
        sha1sum = hasher.hexdigest()

    blob.sha1sum = sha1sum
    blob.file_modified = int(os.path.getmtime(str(filepath)))

    f = open(filepath, "rb")
    blob.file.save(filename, File(f))


def handle_s3_info_image(s3_resource, s3_bucket, blob, file_path, cover_filename):

    filepath = Path(__file__).parent / file_path
    width, height = Image.open(filepath).size

    filepath_cover = Path(__file__).parent / f"blob/tests/resources/{cover_filename}"
    width_cover, height_cover = Image.open(filepath_cover).size

    key = blob.get_s3_key()

    s3_object = s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, key)
    s3_object.metadata.update({"image-width": str(width), "image-height": str(height)})
    s3_object.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}, Metadata=s3_object.metadata, MetadataDirective="REPLACE")

    # "Upload" a cover for the image to S3
    s3_resource.meta.client.upload_file(
        str(filepath_cover),
        settings.AWS_STORAGE_BUCKET_NAME,
        f"{settings.MEDIA_ROOT}/{blob.sha1sum[:2]}/{blob.sha1sum}/{cover_filename}",
        ExtraArgs={'Metadata': {"image-width": str(width_cover),
                                "image-height": str(height_cover),
                                "cover-image": "Yes"}}
    )


def handle_s3_info_pdf(s3_resource, s3_bucket, blob, file_path, cover_filename):

    filepath_cover = Path(__file__).parent / f"blob/tests/resources/{cover_filename}"
    width_cover, height_cover = Image.open(filepath_cover).size

    # "Upload" a cover for the image to S3
    s3_resource.meta.client.upload_file(
        str(filepath_cover),
        settings.AWS_STORAGE_BUCKET_NAME,
        f"{settings.MEDIA_ROOT}/{blob.sha1sum[:2]}/{blob.sha1sum}/{cover_filename}",
        ExtraArgs={'Metadata': {"image-width": str(width_cover),
                                "image-height": str(height_cover),
                                "cover-image": "Yes"}}
    )
