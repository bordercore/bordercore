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

    def element_has_focus(self, element, selector):
        try:
            active_element = self.browser.switch_to.active_element
            target_element = element.find_element(*selector)
            return active_element == target_element
        except:
            return False

    def wait_for_focus(self, element, selector):
        wait = WebDriverWait(self.browser, timeout=10)
        wait.until(lambda driver: self.element_has_focus(element, selector))
