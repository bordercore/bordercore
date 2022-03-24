import time

import pytest

from django.urls import reverse

try:
    from .pages.drill import SummaryPage
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.mark.parametrize("login", [reverse("drill:list")], indirect=True)
def test_tag_search(question, login, live_server, browser, settings):

    tag_name = question[0].tags.all().first().name

    page = SummaryPage(browser)

    # Wait for the Vue front-end to load
    time.sleep(1)

    element = page.study_button()
    element.click()

    time.sleep(1)

    element = page.tag_radio_option()
    element.click()

    element = page.tag_input()
    element.send_keys(tag_name)

    time.sleep(2)

    element = page.tag_dropdown_option(tag_name)
    element.click()

    time.sleep(1)

    element = page.start_study_session_button()
    element.click()

    time.sleep(2)

    element = page.question_text()
    assert element == question[0].question.replace("\n", " ")

    element = page.breadcrumb()
    assert element == "django"
