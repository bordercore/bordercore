from blob.services import get_recent_blobs, parse_date, parse_shortcode


def test_get_recent_blos(auto_login_user, blob_image_factory, blob_text_factory):

    user, _ = auto_login_user()

    blob_list, doctypes = get_recent_blobs(user)

    assert doctypes["image"] == 1
    assert doctypes["document"] == 3
    assert doctypes["all"] == 4

    assert blob_image_factory[0].name in [
        x["name"]
        for x in
        blob_list
    ]

    assert blob_text_factory[0].name in [
        x["name"]
        for x in
        blob_list
    ]


def test_parse_shortcode():

    assert parse_shortcode("https://www.instagram.com/p/CUA4IQcARX2/") == "CUA4IQcARX2"

    assert parse_shortcode("https://www.instagram.com/tv/CWbejF6DD9B/") == "CWbejF6DD9B"

    assert parse_shortcode("https://www.instagram.com/p/CWixXZTLWgf/?utm_source=ig_web_copy_link") == "CWixXZTLWgf"

    assert parse_shortcode("https://www.artstation.com/artwork/0XQTnK") == "0XQTnK"

    try:
        parse_shortcode("https://www.instagram.com/42/")
    except Exception:
        pass
    else:
        assert False, "Bogus shortcode should raise exception"


def test_parse_date():

    assert parse_date("2021-08-15 23:40:56") == "2021-08-15"
    assert parse_date("2021-11-15T15:56:23.875-06:00") == "2021-11-15"
    assert parse_date("January 1, 2022") == "January 1, 2022"
