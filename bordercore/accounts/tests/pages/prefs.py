try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass

from selenium.webdriver.support.ui import Select

from django.urls import reverse


class PrefsPage:

    URL = reverse("accounts:prefs")

    TITLE = (By.TAG_NAME, "title")
    UPDATE_BUTTON = (By.XPATH, "//input[@value='Update']")
    THEME_SELECTED = (By.XPATH, "//select[@id='id_theme']/option[@selected]")
    FAVORITE_TAGS_INPUT = (By.XPATH, "//div[@id='id_favorite_tags']//ul//input")
    PREFS_UPDATED_MESSAGE = (By.XPATH, "//div[@class='alert alert-success'][normalize-space(text())='Preferences updated']")
    DEFAULT_THEME = (By.XPATH, "//select[@id='id_theme']/option[@selected]")
    DEFAULT_COLLECTION_SELECTED = (By.XPATH, "//select[@id='id_homepage_default_collection']/option[@selected]")
    FAVORITE_TAGS = (By.XPATH, "//div[@id='id_favorite_tags']//li[@class='ti-tag ti-valid']")

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
        select = Select(self.browser.find_element_by_id("id_theme"))
        select.select_by_visible_text(theme_name)

    def choose_default_collection(self, collection_name):
        """
        Select a 'Default collection'
        """
        select = Select(self.browser.find_element_by_id("id_homepage_default_collection"))
        select.select_by_visible_text(collection_name)

    def add_favorite_tags(self, tag_name):
        favorite_tags_input = self.browser.find_element(*self.FAVORITE_TAGS_INPUT)
        favorite_tags_input.send_keys(tag_name + Keys.ENTER)

    def selected_theme(self):
        selected_option = self.browser.find_element(*self.THEME_SELECTED).text
        return selected_option

    def selected_default_collection(self):
        selected_option = self.browser.find_element(*self.DEFAULT_COLLECTION_SELECTED).text
        return selected_option

    def update(self):
        """
        Click the 'Update' button
        """
        update_input = self.browser.find_element(*self.UPDATE_BUTTON)
        update_input.click()

    def prefs_updated_message_count(self):
        """
        Find the success message after updating preference options
        """
        message = self.browser.find_elements(*self.PREFS_UPDATED_MESSAGE)
        return len(message)

    def favorite_tags(self):
        selected_option = self.browser.find_element(*self.FAVORITE_TAGS)
        return selected_option.text
