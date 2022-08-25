try:
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass

class SummaryPage:

    STUDY_BUTTON = (By.CSS_SELECTOR, "button[data-bs-target='#modal-study']")
    TAG_RADIO_OPTION = (By.CSS_SELECTOR, "input[value='tag-needing-review']")
    TAG_INPUT = (By.CSS_SELECTOR, "#tag-name input")
    START_STUDY_SESSION_BUTTON = (By.CSS_SELECTOR, "#start-study-session")
    TAG_DROPDOWN = (By.CSS_SELECTOR, "#tag-name ul li")
    QUESTION = (By.CSS_SELECTOR, "h3.drill-text p")
    BREADCRUMB = (By.CSS_SELECTOR, ".breadcrumb-item strong:first-child")

    def __init__(self, browser):
        self.browser = browser

    def study_button(self):
        """
        Find the 'Study' button
        """
        return self.browser.find_element(*self.STUDY_BUTTON)

    def tag_radio_option(self):
        """
        Find the 'Tag' study method option
        """
        return self.browser.find_element(*self.TAG_RADIO_OPTION)

    def tag_input(self):
        """
        Find the 'Tag' text input
        """
        return self.browser.find_element(*self.TAG_INPUT)

    def start_study_session_button(self):
        """
        Find the 'Start Study Session' button
        """
        return self.browser.find_element(*self.START_STUDY_SESSION_BUTTON)

    def tag_dropdown_option(self, tag_name):
        """
        Find the dropdown option with display name 'tag_name'
        """
        tag_list = self.browser.find_elements(*self.TAG_DROPDOWN)

        for option in tag_list:
            if option.text == tag_name:
                return option

    def question_text(self):
        """
        Find the question text
        """
        return self.browser.find_element(*self.QUESTION).text

    def breadcrumb(self):
        """
        Find the breadcrumb text
        """
        return self.browser.find_element(*self.BREADCRUMB).text
