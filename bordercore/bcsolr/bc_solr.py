import solr

host = "localhost"
port = 8080
core = "test"

class BCSolr:

    def __init__(self, solr_host="localhost", solr_port=8080, solr_core="test"):
        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_core = solr_core
        self.s = solr.SolrConnection("http://%s:%d/solr/%s" % (self.solr_host, self.solr_port, self.solr_core))

    def search(self, term, field="title"):
            return self.s.query('%s:%s' % (field,term))
#            for hit in response.results:
#                print hit['title']

if __name__ == '__main__':
    mysolr = BCSolr()
    mysolr.search("lucene")
    response = mysolr.search("Erik Hatcher", "author")
    for hit in response.results:
        print hit['title']
    # add a document to the index
    # mysolr.s.add(id=1, title='Lucene in Action', author=['Erik Hatcher', 'Otis Gospodnetic'])
    # mysolr.s.commit()
