from blob.services import parse_date, parse_shortcode


def test_parse_shortcode():

    assert parse_shortcode("https://www.instagram.com/p/CUA4IQcARX2/") == "CUA4IQcARX2"

    assert parse_shortcode("https://www.instagram.com/tv/CWbejF6DD9B/") == "CWbejF6DD9B"

    assert parse_shortcode("https://www.instagram.com/p/CWixXZTLWgf/?utm_source=ig_web_copy_link") == "CWixXZTLWgf"

    assert parse_shortcode("https://www.artstation.com/artwork/0XQTnK") == "0XQTnK"

    try:
        parse_shortcode("https://www.instagram.com/bogus/")
    except Exception:
        pass
    else:
        assert False, "Bogus shortcode should raise exception"


def test_parse_date():

    assert parse_date("2021-08-15 23:40:56") == "2021-08-15"

    assert parse_date("2021-11-15T15:56:23.875-06:00") == "2021-11-15"
