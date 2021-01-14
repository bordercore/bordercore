from urllib.parse import urlparse

import pytest

from django import urls

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("blob", [pytest.lazy_fixture("blob_image_factory"), pytest.lazy_fixture("blob_text_factory")])
def test_blob_detail(auto_login_user, blob):
    """Verify we redirect to the memes page when a user is logged in"""

    _, client = auto_login_user()

    url = urls.reverse("blob:detail", args=(blob.uuid,))
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    if blob.title == "Vaporwave Wallpaper 2E":
        sha1sum = soup.select("small#sha1sum")[0].text.strip()
        assert sha1sum == blob.sha1sum

    assert soup.select("div#left-block h1#title")[0].text == blob.get_title(remove_edition_string=True)

    url = [x.value for x in blob.metadata_set.all() if x.name == "Url"][0]
    assert soup.select("strong a")[0].text == urlparse(url).netloc

    author = [x.value for x in blob.metadata_set.all() if x.name == "Author"][0]
    assert soup.select("span#author")[0].text == author

    assert soup.select("div#blob_detail_content")[0].text.strip() == blob.content

    assert soup.select("div#blob_note")[0].text.strip() == blob.note

    assert soup.select("span.metadata_value")[0].text == "John Smith, Jane Doe"
