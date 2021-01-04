try:
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testuser"


class LoginPage:
    USERNAME_INPUT = (By.NAME, "username")
    PASSWORD_INPUT = (By.NAME, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    def __init__(self, browser):
        self.browser = browser

    def load(self, live_server):
        self.browser.get(f"{live_server.url}/accounts/login/?next=/")

    def login(self):
        username_input = self.browser.find_element(*self.USERNAME_INPUT)
        username_input.clear()
        username_input.send_keys(TEST_USERNAME)
        password_input = self.browser.find_element(*self.PASSWORD_INPUT)
        password_input.clear()
        password_input.send_keys(TEST_PASSWORD)
        submit_button = self.browser.find_element(*self.SUBMIT_BUTTON)
        submit_button.click()


class HomePage:
    TITLE = (By.TAG_NAME, "title")
    TODO = (By.XPATH, "//div[div[@class='card-title'][normalize-space(text())='Important Tasks']]//li")

    def __init__(self, browser):
        self.browser = browser

    def load(self, live_server):
        self.browser.get(f"{live_server.url}/")

    def title_value(self):
        """
        Find the value of the title element
        """
        search_input = self.browser.find_element(*self.TITLE)
        return search_input.get_attribute("innerHTML")

    def todo_count(self):
        """
        Find all important todo tasks
        """
        todo_elements = self.browser.find_elements(*self.TODO)
        return len(todo_elements)
