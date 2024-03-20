try:
    from selenium.webdriver.support.wait import WebDriverWait
except (ModuleNotFoundError, NameError):
    # Don't worry if these imports don't exist in production
    pass


class Page:

    def find_element(self, element, selector, wait=False):
        if wait:
            wait = WebDriverWait(self.browser, timeout=10)
            wait.until(lambda x: x.find_element(*selector))
        return element.find_element(*selector)

    def find_elements(self, element, selector, wait=False):
        if wait:
            wait = WebDriverWait(self.browser, timeout=10)
            wait.until(lambda x: x.find_elements(*selector))
        return element.find_elements(*selector)
