from urllib.parse import quote_plus

import django

django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob  # isort:skip


def test_get_s3_key_from_sha1sum(blob_image_factory):
    s3_key = Blob.get_s3_key_from_sha1sum(blob_image_factory.sha1sum, blob_image_factory.file)
    assert s3_key == f"blobs/{blob_image_factory.sha1sum[:2]}/{blob_image_factory.sha1sum}/{blob_image_factory.file}"


def test_get_urls(blob_image_factory):
    urls = blob_image_factory.get_urls()
    assert urls[0]["domain"] == "www.bordercore.com"
    assert urls[0]["url"] == "https://www.bordercore.com"


def test_get_edition_string(blob_image_factory):

    assert blob_image_factory.get_edition_string() == "Second Edition"

    blob_image_factory.title = "Title"
    assert blob_image_factory.get_edition_string() == ""


def test_get_metadata(blob_image_factory):

    metadata = blob_image_factory.get_metadata()
    assert "John Smith" in [value for key, value in metadata.items()]


def test_get_content_type():
    assert Blob.get_content_type("application/octet-stream") == "Video"
    assert Blob.get_content_type("text/css") == ""


def test_get_parent_dir(blob_image_factory):
    parent_dir = blob_image_factory.get_parent_dir()
    assert parent_dir == f"blobs/{blob_image_factory.sha1sum[:2]}/{blob_image_factory.sha1sum}"


def test_get_url(blob_image_factory):
    url = blob_image_factory.get_url()
    assert url == f"{blob_image_factory.sha1sum[:2]}/{blob_image_factory.sha1sum}/{quote_plus(str(blob_image_factory.file))}"


def test_get_title(blob_image_factory):

    assert blob_image_factory.get_title() == "Vaporwave Wallpaper 2E"
    assert blob_image_factory.get_title(remove_edition_string=True) == "Vaporwave Wallpaper"

    blob_image_factory.title = ""
    assert blob_image_factory.get_title(use_filename_if_present=True) == blob_image_factory.file
    assert blob_image_factory.get_title() == "No title"


def test_get_tags(blob_image_factory):
    assert blob_image_factory.get_tags() == "django, linux, video"


def test_get_collection_info(collection, blob_pdf_factory):
    assert len(blob_pdf_factory.get_collection_info()) == 1
    assert blob_pdf_factory.get_collection_info().first().name == "collection_0"


def test_get_linked_blobs(blob_pdf_factory):
    assert len(blob_pdf_factory.get_linked_blobs()) == 0


def test_get_date(blob_image_factory):
    assert blob_image_factory.get_date() == "March 04, 2021"


def test_get_detail_page_metadata(blob_image_factory):
    assert blob_image_factory.get_detail_page_metadata() == {"Artist": "John Smith, Jane Doe"}


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
    assert cover_info["url"] == "https://blobs.bordercore.com/1c/1ce691807b81b83c89c157f89de08da3815bb550/cover.jpg"

    cover_info_pdf = blob_pdf_factory.get_cover_info()
    assert cover_info_pdf["url"] == "https://blobs.bordercore.com/c3/c315bac6f171d8e9cf52613d89a950b5161d8c16/cover-large.jpg"

    cover_info_pdf = blob_pdf_factory.get_cover_info(size="small")
    assert cover_info_pdf["url"] == "https://blobs.bordercore.com/c3/c315bac6f171d8e9cf52613d89a950b5161d8c16/cover.jpg"

    assert Blob.get_cover_info_static(blob_pdf_factory.user, None) == {"url": ""}
