import pytest

try:
    from .pages.homepage import HomePage, LoginPage
    from selenium import webdriver
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass

pytestmark = pytest.mark.functional


@pytest.fixture(scope="session")
def browser():

    driver = webdriver.Firefox(executable_path="/opt/bin/geckodriver")

    # Fails with "Message: Service /opt/google/chrome/chrome unexpectedly exited. Status code was: 0"
    # driver = webdriver.Chrome(executable_path="/opt/google/chrome/chrome")

    yield driver

    driver.quit()


@pytest.fixture()
def login(live_server, browser, settings):

    settings.DEBUG = True

    page = LoginPage(browser)
    page.load(live_server)
    page.login()


def test_homepage(bookmark, todo, login, live_server, browser, settings):

    settings.DEBUG = True

    page = HomePage(browser)

    assert page.title_value() == "Bordercore :: Homepage"

    # There should be two important todo tasks
    assert page.todo_count() == 2

    # There should be three recent bookmarks
    assert page.bookmarks_count() == 3

    # There should be one pinned bookmark
    assert page.pinned_bookmarks_count() == 1
