
from lib.util import is_image, is_pdf


def test_util_is_image():

    file = "path/to/file.png"
    assert is_image(file) is True

    file = "path/to/file.gif"
    assert is_image(file) is True

    file = "path/to/file.jpg"
    assert is_image(file) is True

    file = "path/to/file.jpeg"
    assert is_image(file) is True

    file = "file.png"
    assert is_image(file) is True

    file = "path/to/file.pdf"
    assert is_image(file) is False


def test_util_is_pdf():

    file = "path/to/file.pdf"
    assert is_pdf(file) is True

    file = "path/to/file.gif"
    assert is_pdf(file) is False
