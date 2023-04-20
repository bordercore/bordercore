import time

from selenium.webdriver.support.ui import Select

from django.urls import reverse

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass


class PrefsPage:

    URL = reverse("accounts:prefs")

    TITLE = (By.TAG_NAME, "title")
    THEME_ID = (By.ID, "id_theme")
    COLLECTION_ID = (By.ID, "id_homepage_default_collection")
    UPDATE_BUTTON = (By.CSS_SELECTOR, "input[value='Update']")
    THEME_SELECTED = (By.CSS_SELECTOR, "select#id_theme option")
    PINNED_TAGS_INPUT = (By.CSS_SELECTOR, "div#id_pinned_tags input")
    PREFS_UPDATED_MESSAGE = (By.CSS_SELECTOR, "div[class='alert alert-success']")
    DEFAULT_COLLECTION_SELECTED = (By.CSS_SELECTOR, "select#id_homepage_default_collection option")
    PINNED_TAGS = (By.CSS_SELECTOR, "div#id_pinned_tags")

    def __init__(self, browser):
        self.browser = browser

    def load(self, live_server):
        self.browser.get(f"{live_server.url}{self.URL}")

    def title_value(self):
        """
        Find the value of the title element
        """
        search_input = self.browser.find_element(*self.TITLE)
        return search_input.get_attribute("innerHTML")

    def choose_theme(self, theme_name):
        """
        Select the 'Dark' theme
        """
        select = Select(self.browser.find_element(*self.THEME_ID))
        select.select_by_visible_text(theme_name)

    def choose_default_collection(self, collection_name):
        """
        Select a 'Default collection'
        """
        select = Select(self.browser.find_element(*self.COLLECTION_ID))
        select.select_by_visible_text(collection_name)

    def add_pinned_tags(self, tag_name):
        pinned_tags_input = self.browser.find_element(*self.PINNED_TAGS_INPUT)
        pinned_tags_input.send_keys(tag_name + Keys.ENTER)
        time.sleep(1)
        pinned_tags_input.send_keys(Keys.ENTER)

    def selected_theme(self):
        options = self.browser.find_elements(*self.THEME_SELECTED)
        return [x for x in options if x.is_selected()][0].text

    def selected_default_collection(self):
        # selected_option = self.browser.find_element(*self.DEFAULT_COLLECTION_SELECTED).text
        options = self.browser.find_elements(*self.DEFAULT_COLLECTION_SELECTED)
        return [x for x in options if x.is_selected()][0].text

    def update(self):
        """
        Click the 'Update' button
        """
        update_input = self.browser.find_element(*self.UPDATE_BUTTON)

        # Scroll the page to avoid 'Element...could not be scrolled into view' error
        self.browser.execute_script("arguments[0].scrollIntoView();", update_input)
        time.sleep(1)

        update_input.click()

    def prefs_updated_message(self):
        """
        Find the success message after updating preference options
        """
        message = self.browser.find_element(*self.PREFS_UPDATED_MESSAGE)
        return message.text

    def pinned_tags(self):
        selected_option = self.browser.find_element(*self.PINNED_TAGS)
        return selected_option.text
