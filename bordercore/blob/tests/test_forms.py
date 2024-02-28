from pathlib import Path
from unittest.mock import Mock

from faker import Factory as FakerFactory

from django.core.files.uploadedfile import SimpleUploadedFile

from blob.forms import BlobForm

faker = FakerFactory.create()


def test_blob_form_add(auto_login_user, blob_pdf_factory):

    user, _ = auto_login_user()

    mock_request = Mock()
    mock_request.user = user

    file_path = Path(__file__).parent / "resources/test_blob.jpg"
    with open(file_path, "rb") as f:
        file_blob = f.read()
    file_upload = SimpleUploadedFile(file_path.name, file_blob)

    form_data = {
        "date": faker.date(),
        "name": faker.text(max_nb_chars=10),
        "filename": faker.file_name(extension="jpg"),
        "file": file_upload,
        "tags": "django, linux"
    }
    form = BlobForm(data=form_data, files={"file": file_upload}, request=mock_request)
    assert form.is_valid()

    # Test invalid date format.
    form_data = {
        "date": "Bogus date format",
        "name": faker.text(max_nb_chars=10),
        "filename": faker.file_name(extension="jpg"),
        "file": file_upload,
        "tags": "django, linux"
    }
    form = BlobForm(data=form_data, request=mock_request)
    assert not form.is_valid()
    assert len(form.errors) == 1

    # Test invalid file name.
    form_data = {
        "date": faker.date(),
        "name": faker.text(max_nb_chars=10),
        "filename": "cover.jpg",
        "file": file_upload,
        "tags": "django, linux"
    }
    form = BlobForm(data=form_data, request=mock_request)
    assert not form.is_valid()
    assert len(form.errors) == 1

    # Test adding a duplicate blob file.
    # This is the same blob used in the blob_pdf_factory fixture,
    #  which should generate a form error.
    file_upload = SimpleUploadedFile(blob_pdf_factory[0].file.name, blob_pdf_factory[0].file.read())

    form_data = {
        "date": faker.date(),
        "name": faker.text(max_nb_chars=10),
        "filename": faker.file_name(extension="jpg"),
        "file": file_upload,
        "tags": "django, linux"
    }
    form = BlobForm(data=form_data, files={"file": file_upload}, request=mock_request)
    assert not form.is_valid()
    assert len(form.errors) == 1
