import os

from solrpy.core import utc_from_string

from lib.time_utils import get_relative_date


class SolrResultSet():

    filename = None

    def __init__(self, result_set):
        self.result_set = result_set
        self.file_path = result_set.get('filepath', '')
        if self.file_path:
            self.filename = os.path.basename(self.file_path)

    def get_filename(self):
        try:
            filename = os.path.basename(self.result_set['filepath'])
        except KeyError:
            filename = None
        return filename

    def get_last_modified(self):
        try:
            last_modified = self.result_set['last_modified']
        except KeyError:
            return ''
        return get_relative_date(utc_from_string(last_modified))

    def get_title(self):
        try:
            title = self.result_set['title'][0]
        except KeyError:
            if self.filename:
                title = self.filename
            else:
                title = "No title"

        return title
