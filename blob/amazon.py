import requests

from amazonproduct import API
from amazonproduct.errors import NoExactMatchesFound

config = {
}


class AmazonMixin(object):

    def __init__(self):
        self.api = API(locale='us')

    def get_amazon_cover_url(self, index=0):
        title = self.get_title(remove_edition_string=True)
        author = self.metadata_set.filter(name='Author')[0].value

        try:
            results = self.api.item_search('Books', Title=title, Author=author, ResponseGroup='Images', Sort='-publication_date')
        except NoExactMatchesFound:
            return None

        for index_loop, result in enumerate(results):
            if index_loop == index:
                return {'small': str(result.SmallImage.URL),
                        'medium': str(result.MediumImage.URL),
                        'large': str(result.LargeImage.URL),
                        'count': sum(1 for _ in results)}

    def set_amazon_cover_url(self, size, url):
        r = requests.get(str(url))
        image_filename = "%s/cover-%s.jpg" % (self.get_parent_dir(), size)
        if r.status_code == 200:
            f = open(image_filename, 'w')
            f.write(r.content)
