import os

import boto3
import botocore
import pytest

import django
from django.conf import settings

try:
    from moto import mock_s3
except ModuleNotFoundError:
    pass


django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Document  # isort:skip


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def s3_resource(aws_credentials):
    """Mocked S3 Fixture."""

    with mock_s3():
        yield boto3.resource(service_name="s3")


@pytest.fixture(scope="function")
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


def test_get_s3_key_from_sha1sum(blob_image):
    s3_key = Document.get_s3_key_from_sha1sum(blob_image.sha1sum, blob_image.file)
    assert s3_key == f"blobs/{blob_image.sha1sum[:2]}/{blob_image.sha1sum}/{blob_image.file}"


def test_get_urls(blob_image):
    urls = blob_image.get_urls()
    assert urls[0]["domain"] == "www.bordercore.com"
    assert urls[0]["url"] == "https://www.bordercore.com"


def test_get_metadata(blob_image):
    metadata = blob_image.get_metadata()
    assert "John Smith" in [value for key, value in metadata.items()]


def test_get_content_type():
    assert Document.get_content_type("application/octet-stream") == "Video"
    assert Document.get_content_type("text/css") == ""


def test_get_parent_dir(blob_image):
    parent_dir = blob_image.get_parent_dir()
    assert parent_dir == f"blobs/{blob_image.sha1sum[:2]}/{blob_image.sha1sum}"


def test_get_url(blob_image):
    url = blob_image.get_url()
    assert url == f"{blob_image.sha1sum[:2]}/{blob_image.sha1sum}/{blob_image.file}"


# @mock.patch("os.path.basename")
# def test_get_title(blob_image, mocker):
def test_get_title(blob_image):

    # TODO: Do we need this? If not, we can remove 'mocker' as an argument
    # mocker.return_value = blob_image.file

    assert blob_image.get_title() == "Vaporwave Wallpaper 2E"
    assert blob_image.get_title(remove_edition_string=True) == "Vaporwave Wallpaper"

    blob_image.title = ""
    assert blob_image.get_title(use_filename_if_present=True) == blob_image.file
    assert blob_image.get_title() == "No title"


def test_get_edition_string(blob_image):
    assert blob_image.get_edition_string() == "Second Edition"

    blob_image.title = "Title"
    assert blob_image.get_edition_string() == ""


def test_get_tags(blob_image):
    assert blob_image.get_tags() == "django, linux"


def test_is_ingestible_file(blob_image):
    assert Document.is_ingestible_file("file.png") is False
    assert Document.is_ingestible_file("file.pdf") is True


def test_get_cover_info(blob_image, blob_pdf):

    cover_info = Document.get_cover_info(blob_image.user, blob_image.sha1sum)
    assert cover_info["height"] == 1689
    assert cover_info["width"] == 1600

    cover_info = Document.get_cover_info(blob_image.user, blob_image.sha1sum, size="small")
    assert cover_info["url"] == f"{blob_image.get_parent_dir()}/cover.jpg"

    cover_info_pdf = Document.get_cover_info(blob_pdf.user, blob_pdf.sha1sum)
    assert cover_info_pdf["url"] == f"{blob_pdf.get_parent_dir()}/cover-large.jpg"
    cover_info_pdf = Document.get_cover_info(blob_pdf.user, blob_pdf.sha1sum, size="small")
    assert cover_info_pdf["url"] == f"{blob_pdf.get_parent_dir()}/cover.jpg"

    assert Document.get_cover_info(blob_pdf.user, None) == {}
