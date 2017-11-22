import os


class SolrResultSet():

    filename = None

    def __init__(self, result_set):
        self.result_set = result_set
        self.file_path = result_set.get('filepath', '')
        if self.file_path:
            self.filename = os.path.basename(self.file_path)

    def get_title(self):
        try:
            title = self.result_set['title'][0]
        except KeyError:
            if self.filename:
                title = self.filename
            else:
                title = "No title"

        return title
