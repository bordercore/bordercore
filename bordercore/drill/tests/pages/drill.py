class SummaryPage:

    STUDY_BUTTON = "button[data-bs-target='#modal-study']"
    TAG_RADIO_OPTION = "input[value='tag-needing-review']"
    TAG_INPUT = "#tag-name input"
    START_STUDY_SESSION_BUTTON = "start-study-session"
    TAG_DROPDOWN = "#tag-name ul li"
    QUESTION = "h3.drill-text p"
    BREADCRUMB = ".breadcrumb-item strong:first-child"

    def __init__(self, browser):
        self.browser = browser

    def study_button(self):
        """
        Find the 'Study' button
        """
        return self.browser.find_element_by_css_selector(self.STUDY_BUTTON)

    def tag_radio_option(self):
        """
        Find the 'Tag' study method option
        """
        return self.browser.find_element_by_css_selector(self.TAG_RADIO_OPTION)

    def tag_input(self):
        """
        Find the 'Tag' text input
        """
        return self.browser.find_element_by_css_selector(self.TAG_INPUT)

    def start_study_session_button(self):
        """
        Find the 'Start Study Session' button
        """
        return self.browser.find_element_by_id(self.START_STUDY_SESSION_BUTTON)

    def tag_dropdown_option(self, tag_name):
        """
        Find the dropdown option with display name 'tag_name'
        """
        tag_list = self.browser.find_elements_by_css_selector(self.TAG_DROPDOWN)

        for option in tag_list:
            if option.text == tag_name:
                return option

    def question_text(self):
        """
        Find the question text
        """
        return self.browser.find_element_by_css_selector(self.QUESTION).text

    def breadcrumb(self):
        """
        Find the breadcrumb text
        """
        return self.browser.find_element_by_css_selector(self.BREADCRUMB).text
