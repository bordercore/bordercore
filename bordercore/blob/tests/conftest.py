import hashlib
import os
from pathlib import Path

import pytest
from PIL import Image

import django
from django.conf import settings
from django.core.files import File

django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Document, MetaData  # isort:skip


@pytest.fixture(scope="function")
def blob_image(s3_resource, s3_bucket, user, db):

    # TODO: Is there a way to only have this fixture called once, eg "module" scope?
    #  I can't use "module" scope because it conflicts with the "db" fixture scope

    filepath = Path(__file__).parent / "resources/test_blob.jpg"
    filename = Path(filepath).name
    width, height = Image.open(filepath).size

    filepath_cover = Path(__file__).parent / "resources/cover.jpg"
    width_cover, height_cover = Image.open(filepath_cover).size

    hasher = hashlib.sha1()
    with open(filepath, "rb") as f:
        buf = f.read()
        hasher.update(buf)
        sha1sum = hasher.hexdigest()

    blob = Document.objects.create(
        sha1sum=sha1sum,
        title="Vaporwave Wallpaper 2E",
        content="This is sample content",
        note="This is a sample note",
        user=user)

    key = f"{settings.MEDIA_ROOT}/{sha1sum[:2]}/{sha1sum}/{filename}"

    blob.file_modified = int(os.path.getmtime(str(filepath)))

    f = open(filepath, "rb")
    blob.file.save(filename, File(f))

    s3_object = s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, key)
    s3_object.metadata.update({"image-width": str(width), "image-height": str(height)})
    s3_object.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}, Metadata=s3_object.metadata, MetadataDirective="REPLACE")

    # "Upload" a cover for the image to S3
    s3_resource.meta.client.upload_file(
        str(filepath_cover),
        settings.AWS_STORAGE_BUCKET_NAME,
        f"{settings.MEDIA_ROOT}/{sha1sum[:2]}/{sha1sum}/cover.jpg",
        ExtraArgs={'Metadata': {"image-width": str(width_cover),
                                "image-height": str(height_cover),
                                "cover-image": "Yes"}}
    )

    tag1, created = Tag.objects.get_or_create(name="django")
    tag2, created = Tag.objects.get_or_create(name="linux")
    blob.tags.add(tag1, tag2)

    MetaData.objects.create(
        user=user,
        name="Url",
        value="https://www.bordercore.com",
        blob=blob)

    MetaData.objects.create(
        user=user,
        name="Author",
        value="John Smith",
        blob=blob)

    MetaData.objects.create(
        user=user,
        name="Artist",
        value="John Smith",
        blob=blob)

    MetaData.objects.create(
        user=user,
        name="Artist",
        value="Jane Doe",
        blob=blob)

    yield blob


@pytest.fixture(scope="function")
def blob_pdf(s3_resource, s3_bucket, user, db):

    # TODO: Is there a way to only have this fixture called once, eg "module" scope?
    #  I can't use "module" scope because it conflicts with the "db" fixture scope
    print("blob fixture called")

    filepath = Path(__file__).parent / "resources/test_blob.pdf"
    filename = Path(filepath).name

    filepath_cover_large = Path(__file__).parent / "resources/cover-large.jpg"
    width_cover, height_cover = Image.open(filepath_cover_large).size

    hasher = hashlib.sha1()
    with open(filepath, "rb") as f:
        buf = f.read()
        hasher.update(buf)
        sha1sum = hasher.hexdigest()

    blob = Document.objects.create(
        sha1sum=sha1sum,
        title="Bleached Album Notes",
        user=user)

    blob.file_modified = int(os.path.getmtime(str(filepath)))

    f = open(filepath, "rb")
    blob.file.save(filename, File(f))

    # "Upload" a cover for the image to S3
    s3_resource.meta.client.upload_file(
        str(filepath_cover_large),
        settings.AWS_STORAGE_BUCKET_NAME,
        f"{settings.MEDIA_ROOT}/{sha1sum[:2]}/{sha1sum}/cover-large.jpg",
        ExtraArgs={'Metadata': {"image-width": str(width_cover),
                                "image-height": str(height_cover),
                                "cover-image": "Yes"}}
    )

    tag1, created = Tag.objects.get_or_create(name="django")
    tag2, created = Tag.objects.get_or_create(name="linux")
    blob.tags.add(tag1, tag2)

    yield blob
