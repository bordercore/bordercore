from django import urls


def test_album_viewset(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("album-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("album-detail", kwargs={"uuid": song[0].album.uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_blob_viewset(auto_login_user, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("blob-detail", kwargs={"uuid": blob_image_factory[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_sha1sum_viewset(auto_login_user, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("sha1sum-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("sha1sum-detail", kwargs={"sha1sum": blob_image_factory[0].sha1sum})
    resp = client.get(url)
    assert resp.status_code == 200


def test_bookmark_viewset(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("bookmark-detail", kwargs={"uuid": bookmark[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_collection_viewset(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("collection-detail", kwargs={"uuid": collection[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_feed_viewset(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("feed-detail", kwargs={"uuid": feed[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_feeditem_viewset(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feeditem-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("feeditem-detail", kwargs={"pk": feed[0].feeditem_set.first().id})
    resp = client.get(url)
    assert resp.status_code == 200


def test_question_viewset(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("question-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("question-detail", kwargs={"uuid": question[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_playlist_viewset(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("playlist-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("playlist-detail", kwargs={"uuid": playlist[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_playlistitem_viewset(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("playlistitem-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("playlistitem-detail", kwargs={"uuid": playlist[0].playlistitem_set.first().uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_song_viewset(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("song-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("song-detail", kwargs={"uuid": song[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_songsource_viewset(auto_login_user, song_source):

    _, client = auto_login_user()

    url = urls.reverse("songsource-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("songsource-detail", kwargs={"pk": song_source.id})
    resp = client.get(url)
    assert resp.status_code == 200


def test_tag_viewset(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tag-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("tag-detail", kwargs={"pk": tag[0].id})
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("tagname-detail", kwargs={"name": tag[0].name})
    resp = client.get(url)
    assert resp.status_code == 200


def test_tagalias_viewset(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tagalias-list")
    resp = client.get(url)
    assert resp.status_code == 200


def test_todo_viewset(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo-list")
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("todo-detail", kwargs={"uuid": todo.uuid})
    resp = client.get(url)
    assert resp.status_code == 200
