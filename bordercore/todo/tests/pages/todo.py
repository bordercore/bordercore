try:
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:
    # Don't worry if this import doesn't exist in production
    pass


class TodoPage:

    TITLE = (By.TAG_NAME, "title")
    TODO_ELEMENTS = (By.XPATH, "//div[@id='vue-app']//table/tbody/tr")
    FIRST_TASK = (By.XPATH, "//div[@id='vue-app']//table/tbody/tr[1]/td[2]/span")
    NO_TASKS = (By.XPATH, "//div[@id='vue-app']//table/tbody/tr[1]/td[1]/div/div")
    PRIORITY_COLUMN = (By.XPATH, "//div[@id='vue-app']//table/thead/tr/th[@class='todo-col-priority']")
    MEDIUM_PRIORITY_FILTER = (By.CSS_SELECTOR, "div[data-priority='2']")

    def __init__(self, browser):
        self.browser = browser

    def title_value(self):
        """
        Find the value of the title element
        """
        search_input = self.browser.find_element(*self.TITLE)
        return search_input.get_attribute("innerHTML")

    def todo_count(self):
        """
        Find all todo tasks bookmarks
        """
        todo_elements = self.browser.find_elements(*self.TODO_ELEMENTS)
        return len(todo_elements)

    def todo_task_text(self):
        """
        Find the text of the first ask
        """
        todo_element = self.browser.find_elements(*self.FIRST_TASK)
        return todo_element[0].get_attribute("innerHTML")

    def todo_no_tasks_text(self):
        """
        Find the text of the first ask
        """
        todo_element = self.browser.find_elements(*self.NO_TASKS)
        return todo_element[0].get_attribute("innerHTML")

    def sort_by_priority(self):

        priority_column = self.browser.find_element(*self.PRIORITY_COLUMN)
        priority_column.click()

        todo_element = self.browser.find_elements(*self.FIRST_TASK)
        return todo_element[0].get_attribute("innerHTML")

    def medium_priority_filter(self):
        """
        """
        todo_element = self.browser.find_elements(*self.MEDIUM_PRIORITY_FILTER)
        return todo_element[0]
