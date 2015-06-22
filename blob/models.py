import json
import os
import os.path

from django.contrib.auth.models import User
from django.db import models
from lib.mixins import TimeStampedModel
import solr

from tag.models import Tag

SOLR_HOST = 'localhost'
SOLR_PORT = 8080
SOLR_COLLECTION = 'solr/bordercore'


class Blob(TimeStampedModel):
    """
    A blob belonging to a user.
    """
    EBOOK_DIR = '/home/media/ebooks'
    BLOB_STORE = '/home/media/blobs'

    sha1sum = models.CharField(max_length=40, unique=True)
    filename = models.TextField()
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_parent_dir(self):
        return "%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum)

    def get_url(self):
        return "%s/%s/%s" % (self.sha1sum[0:2], self.sha1sum, self.filename)

    def get_title(self):
        m = self.metadata_set.filter(name='Title')
        if m:
            return m[0].value
        else:
            return "No title"

    def get_cover_url(self, size='medium'):

        for image_type in ['jpg', 'png']:
            if os.path.isfile("%s/cover-%s.%s" % (self.get_parent_dir(), size, image_type)):
                return "%s/%s/cover-%s.%s" % (self.sha1sum[0:2], self.sha1sum, size, image_type)
        return None

    def get_solr_info(self):
        conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION))
        solr_args = {'q': 'sha1sum:%s' % self.sha1sum, 'wt': 'json', 'fl': 'content_type'}
        return json.loads(conn.raw_query(**solr_args))['response']

    def delete(self):
        file_path = "%s/%s" % (self.get_parent_dir(), self.filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            # Delete the parent dir if this is not an ebook
            os.rmdir("%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum))
            # If the parent of that is empty, delete it, too
            parent_dir = "%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2])
            if os.listdir(parent_dir) == []:
                os.rmdir(parent_dir)
            super(Blob, self).delete()
        else:
            raise Exception("File does not exist: %s" % file_path)

    def get_content_type(self, argument):
        switcher = {
            "application/pdf": "PDF",
            "image/jpeg": "Image",
            "image/png": "Image"
        }

        return switcher.get(argument, lambda: argument)


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob)

    class Meta:
        unique_together = ('name', 'value', 'blob')
