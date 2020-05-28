import os
from urllib.parse import urlparse

import boto3
import botocore
import pytest

import django
from django import urls
from django.conf import settings

try:
    from bs4 import BeautifulSoup
    from moto import mock_s3
except ModuleNotFoundError:
    pass


django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob  # isort:skip


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="module")
def s3_resource(aws_credentials):
    """Mocked S3 Fixture."""

    with mock_s3():
        yield boto3.resource(service_name="s3")


@pytest.fixture(scope="module")
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
def user(db, client, django_user_model):
    username = "testuser"
    password = "password"
    email = "testuser@testdomain.com"

    user = django_user_model.objects.create_user(username, email, password)
    client.login(username=username, password=password)

    return user


@pytest.mark.django_db
def test_blob_detail(user, blob_image_factory, client):
    """Verify we redirect to the memes page when a user is logged in"""

    url = urls.reverse("blob_detail", args=(blob_image_factory.uuid,))
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    sha1sum = soup.select("small#sha1sum")[0].text.strip()
    assert sha1sum == blob_image_factory.sha1sum

    assert soup.select("div#left-block h1#title")[0].text == blob_image_factory.get_title(remove_edition_string=True)

    url = [x.value for x in blob_image_factory.metadata_set.all() if x.name == "Url"][0]
    assert soup.select("strong a")[0].text == urlparse(url).netloc

    author = [x.value for x in blob_image_factory.metadata_set.all() if x.name == "Author"][0]
    assert soup.select("span#author")[0].text == author

    assert soup.select("div#content")[0].text.strip() == blob_image_factory.content

    assert soup.select("div#blob_note")[0].text.strip() == blob_image_factory.note

    assert soup.select("span.metadata_value")[0].text == "John Smith, Jane Doe"
