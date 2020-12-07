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

from .factories import BlobFactory

try:
    from moto import mock_s3
except ModuleNotFoundError:
    pass

django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob, MetaData  # isort:skip


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


@pytest.fixture(scope="function")
def blob_image_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        uuid="0bb4914e-cd3c-4d6b-9d72-0454adf00260",
        title="Vaporwave Wallpaper 2E",
        tags=("django", "linux", "video"),
    )

    file_path = "resources/test_blob.jpg"
    cover_filename = "cover.jpg"
    handle_file_info(blob, file_path, cover_filename)
    handle_s3_info_image(s3_resource, s3_bucket, blob, file_path, cover_filename)
    yield blob


@pytest.fixture(scope="function")
def blob_pdf_factory(db, s3_resource, s3_bucket):

    blob = BlobFactory(
        uuid="4158cf58-306c-42d7-9c98-07d3a96a1d8b",
        title="Bleached Album Notes",
        tags=("django", "linux", "video"),
    )

    file_path = "resources/test_blob.pdf"
    cover_filename = "cover-large.jpg"
    handle_file_info(blob, file_path, cover_filename)
    handle_s3_info_pdf(s3_resource, s3_bucket, blob, file_path, cover_filename)
    yield blob


def handle_file_info(blob, file_path, cover_filename):

    filepath = Path(__file__).parent / file_path
    filename = Path(filepath).name

    filepath_cover = Path(__file__).parent / f"resources/{cover_filename}"
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

    filepath_cover = Path(__file__).parent / f"resources/{cover_filename}"
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

    filepath_cover = Path(__file__).parent / f"resources/{cover_filename}"
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
