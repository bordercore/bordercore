from lib.templatetags.domain import domain
from lib.templatetags.favicon import favicon
from lib.templatetags.unescape_em import unescape_em


def test_domain():

    assert domain("") == ""

    assert domain("http://www.bordercore.com/foo") == "www.bordercore.com"
    assert domain("https://www.bordercore.com/foo") == "www.bordercore.com"


def test_favicon():

    assert favicon("") == ""

    assert favicon("http://www.bordercore.com/foo") == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"32\" height=\"32\" />"

    assert favicon("http://www.bordercore.com/foo", 64) == "<img src=\"https://www.bordercore.com/favicons/bordercore.com.ico\" width=\"64\" height=\"64\" />"


def test_unescape_em():

    assert unescape_em("&lt;em&gt;Match&lt;/em&gt;") == "<em>Match</em>"
