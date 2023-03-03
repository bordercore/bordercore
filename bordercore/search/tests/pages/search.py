try:
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass


class SearchPage:

    SEARCH_INPUT = (By.CSS_SELECTOR, "input#search")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "input[type='submit']")
    SEARCH_RESULT_COUNT = (By.CSS_SELECTOR, "h4[class^='search-result-header'] strong")
    SEARCH_RESULT_NAME = (By.CSS_SELECTOR, "li[class*='search-result'] h4 a")
    SEARCH_RESULT_TAG = (By.CSS_SELECTOR, "li a.tag")

    def __init__(self, browser):
        self.browser = browser

    def search_input(self):
        """
        Find the search form input
        """
        return self.browser.find_element(*self.SEARCH_INPUT)

    def submit_button(self):
        """
        Find the form submit button
        """
        return self.browser.find_element(*self.SUBMIT_BUTTON)

    def search_result_count(self):
        """
        Find the text of the first ask
        """
        element = self.browser.find_element(*self.SEARCH_RESULT_COUNT)
        return int(element.get_attribute("innerHTML"))

    def search_result_name(self):
        """
        Find the text of the search result
        """
        element = self.browser.find_element(*self.SEARCH_RESULT_NAME)
        return element.get_attribute("innerHTML")

    def search_result_tag_count(self):
        """
        Find the search result tag count
        """
        return len(self.browser.find_elements(*self.SEARCH_RESULT_TAG))

    def search_result_tags(self):
        """
        Find the search result tag list
        """
        element = self.browser.find_elements(*self.SEARCH_RESULT_TAG)
        return [x.get_attribute("innerHTML") for x in element]


class TagSearchPage:

    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder='Tag']")
    SEARCH_TAG_RESULT = (By.CSS_SELECTOR, "li[class*='search-result']")

    def __init__(self, browser):
        self.browser = browser

    def search_input(self):
        """
        Find the search form input
        """
        return self.browser.find_element(*self.SEARCH_INPUT)

    def search_tag_result_count(self):
        """
        Find the search result tag list
        """
        return len(self.browser.find_elements(*self.SEARCH_TAG_RESULT))


class NoteSearchPage:

    SEARCH_INPUT = (By.CSS_SELECTOR, "#top-search input.multiselect__input")
    SEARCH_RESULT_COUNT = (By.CSS_SELECTOR, "#vue-app ul[class*='note-search-result'] li")
    TOP_SEARCH_ICON = (By.CSS_SELECTOR, "#top-search-icon")

    def __init__(self, browser):
        self.browser = browser

    def top_search_icon(self):
        """
        Find the search form input
        """
        return self.browser.find_element(*self.TOP_SEARCH_ICON)

    def search_input(self):
        """
        Find the search form input
        """
        return self.browser.find_element(*self.SEARCH_INPUT)

    def search_result_count(self):
        """
        Find the search result count
        """
        return len(self.browser.find_elements(*self.SEARCH_RESULT_COUNT))
