from lib.context_processors import (convert_django_to_bootstrap,
                                    has_no_autohide_tag)


def test_convert_django_to_bootstrap():

    assert convert_django_to_bootstrap("error") == "danger"
    assert convert_django_to_bootstrap("error noAutoHide") == "danger"
    assert convert_django_to_bootstrap("debug") == "info"
    assert convert_django_to_bootstrap("noAutoHide debug") == "info"
    assert convert_django_to_bootstrap("info") == "info"
    assert convert_django_to_bootstrap("success") == "success"
    assert convert_django_to_bootstrap("warning") == "warning"


def test_has_no_autohide_tag():

    assert has_no_autohide_tag("noAutoHide") is True
    assert has_no_autohide_tag("noAutoHide info") is True
    assert has_no_autohide_tag("error noAutoHide") is True
    assert has_no_autohide_tag("warning") is False
