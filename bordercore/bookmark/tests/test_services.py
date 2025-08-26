from bookmark.services import get_recent_bookmarks


def test_get_recent_bookmarks(auto_login_user, bookmark):

    user, _ = auto_login_user()

    results = get_recent_bookmarks(user)

    assert len(results) == 5
    assert results[0]["uuid"] == str(bookmark[4].uuid)
    assert results[0]["name"] == bookmark[4].name
