import datetime
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

try:
    from pyvirtualdisplay import Display
    from selenium import webdriver
    from homepage.tests.pages.homepage import LoginPage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

django.setup()

from accounts.models import SortOrderUserTag  # isort:skip
from accounts.tests.factories import TEST_PASSWORD  # isort:skip
from blob.tests.factories import BlobFactory  # isort:skip
from bookmark.tests.factories import BookmarkFactory  # isort:skip
from collection.tests.factories import CollectionFactory  # isort:skip
from drill.tests.factories import QuestionFactory  # isort:skip
from feed.tests.factories import FeedFactory  # isort:skip
from node.models import SortOrderNodeBookmark, SortOrderNodeBlob  # isort:skip
from node.tests.factories import NodeFactory  # isort:skip
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
def blob_image_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        id=1,
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
        id=2,
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
def blob_text_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        id=3,
        uuid="7ef28ad2-ee89-4bf7-8a58-4bdfb74424e2",
        title="Sampe blob with no sha1sum",
        tags=("django"),
    )

    yield blob


@pytest.fixture()
def bookmark(tag):

    bookmark_1 = BookmarkFactory(daily={"viewed": "false"})
    bookmark_2 = BookmarkFactory()
    bookmark_3 = BookmarkFactory(is_pinned=True)
    bookmark_4 = BookmarkFactory()
    bookmark_5 = BookmarkFactory()

    bookmark_3.tags.add(tag[0])
    bookmark_2.tags.add(tag[0])
    bookmark_1.tags.add(tag[0])

    yield [bookmark_1, bookmark_2, bookmark_3, bookmark_4, bookmark_5]


@pytest.fixture(scope="session")
def browser():

    # Set screen resolution to 1366 x 768 like most 15" laptops
    display = Display(visible=0, size=(1366, 768))
    display.start()

    driver = webdriver.Firefox(executable_path="/opt/bin/geckodriver")

    # Fails with "Message: Service /opt/google/chrome/chrome unexpectedly exited. Status code was: 0"
    # driver = webdriver.Chrome(executable_path="/opt/google/chrome/chrome")

    yield driver

    # Quit the Xvfb display
    display.stop()

    driver.quit()


@pytest.fixture()
def login(auto_login_user, live_server, browser, settings, request):

    settings.DEBUG = True

    auto_login_user()

    page = LoginPage(browser)
    page.load(live_server, request.param)
    page.login()


@pytest.fixture()
def feed(auto_login_user):

    user, _ = auto_login_user()

    feed_0 = FeedFactory(name="Hacker News")
    feed_0.subscribe_user(user, 1)
    feed_1 = FeedFactory()
    feed_2 = FeedFactory()

    yield [feed_0, feed_1, feed_2]


@pytest.fixture()
def collection(blob_image_factory, blob_pdf_factory):

    collection = CollectionFactory()

    tag_1 = TagFactory(name="linux")
    tag_2 = TagFactory(name="django")
    collection.tags.add(tag_1, tag_2)

    collection.blob_list = [
        {
            "id": x.id,
            "added": int(datetime.datetime.now().strftime("%s"))
        }
        for x in [blob_image_factory, blob_pdf_factory]
    ]
    collection.save()

    yield collection


@pytest.fixture()
def node(bookmark, blob_image_factory, blob_pdf_factory):

    node = NodeFactory()

    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[0])
    so.save()
    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[1])
    so.save()

    so = SortOrderNodeBlob(node=node, blob=blob_image_factory)
    so.save()
    so = SortOrderNodeBlob(node=node, blob=blob_pdf_factory)
    so.save()

    yield node


@pytest.fixture()
def question(tag):

    question = QuestionFactory()

    question.tags.add(tag[0])
    question.tags.add(tag[1])

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
def sort_order_user_tag(auto_login_user, tag):

    user, _ = auto_login_user()

    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag[0])
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag[1])
    sort_order.save()
    sort_order = SortOrderUserTag(userprofile=user.userprofile, tag=tag[2])
    sort_order.save()


@pytest.fixture()
def tag():

    TagFactory.reset_sequence(0)

    tag_0 = TagFactory(name="django")
    tag_1 = TagFactory(name="video", is_meta=True)
    tag_2 = TagFactory(name="linux")

    yield [tag_0, tag_1, tag_2]


@pytest.fixture()
def todo():

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

    yield task_3


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
