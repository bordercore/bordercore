import requests
from amazonproduct import API
from amazonproduct.errors import NoExactMatchesFound

# Note: be sure the following environment variables are set
#
# AWS_ACCESS_KEY
# AWS_SECRET_ACCESS_KEY
# AWS_ASSOCIATE_TAG


class AmazonMixin(object):

    def __init__(self):
        self.api = API(locale='us')

    def get_amazon_cover_url(self, index=0):

        try:
            title = self.get_title(remove_edition_string=True)
            author = self.metadata_set.filter(name='Author')
            if not author:
                return {'error': 'Error: Amazon API lookup requires an author'}
            results = self.api.item_search('Books', Title=title, Author=author.first().value, ResponseGroup='Images', Sort='-publication_date')
        except NoExactMatchesFound:
            return {'error': 'Error: no matches found from Amazon API'}

        for index_loop, result in enumerate(results):
            if index_loop == index:
                info = {'count': sum(1 for _ in results)}
                try:
                    info['small'] = str(result.SmallImage.URL)
                except:
                    pass
                try:
                    info['large'] = str(result.LargeImage.URL)
                except:
                    pass
                return info

    def set_amazon_cover_url(self, size, url):
        r = requests.get(str(url))
        image_filename = "%s/cover-%s.jpg" % (self.get_parent_dir(), size)
        if r.status_code == 200:
            f = open(image_filename, 'wb')
            f.write(r.content)
