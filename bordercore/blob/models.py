import json
import os
import os.path
from PIL import Image
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from lib.mixins import TimeStampedModel
import solr

from blob.amazon import AmazonMixin
from collection.models import Collection
from tag.models import Tag

EDITIONS = {'1': 'First',
            '2': 'Second',
            '3': 'Third',
            '4': 'Fourth',
            '5': 'Fifth',
            '6': 'Sixth',
            '7': 'Seventh',
            '8': 'Eighth'}

MAX_COVER_IMAGE_WIDTH = 600


class Blob(TimeStampedModel, AmazonMixin):
    """
    A blob belonging to a user.
    """
    EBOOK_DIR = '/home/media/ebooks'
    BLOB_STORE = '/home/media/blobs'

    sha1sum = models.CharField(max_length=40, unique=True)
    filename = models.TextField()
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)
    blobs = models.ManyToManyField("self")
    is_private = models.BooleanField(default=False)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_parent_dir(self):
        return "%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum)

    def get_url(self):
        return "%s/%s/%s" % (self.sha1sum[0:2], self.sha1sum, self.filename)

    def get_title(self, remove_edition_string=False):
        m = self.metadata_set.filter(name='Title')
        if m:
            if remove_edition_string:
                pattern = re.compile('(.*) (\d)E$')
                matches = pattern.match(m[0].value)
                if matches and EDITIONS[matches.group(2)]:
                    return "%s" % (matches.group(1))
            return m[0].value
        else:
            return "No title"

    def get_edition_string(self):
        m = self.metadata_set.filter(name='Title')
        if m:
            pattern = re.compile('(.*) (\d)E$')
            matches = pattern.match(m[0].value)
            if matches and EDITIONS[matches.group(2)]:
                return "%s Edition" % (EDITIONS[matches.group(2)])
        return ""

    @staticmethod
    def get_image_dimensions(file_path, max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        info = {}

        info['width'], info['height'] = Image.open(file_path).size
        if info['width'] > max_cover_image_width:
            info['height_cropped'] = int(max_cover_image_width * info['height'] / info['width'])
            info['width_cropped'] = max_cover_image_width

        return info

    # This is static so that it can be called without a blob object, eg
    #  based on results from a Solr query
    @staticmethod
    def get_cover_info(sha1sum, size='large', max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        info = {}

        parent_dir = "%s/%s/%s" % (Blob.BLOB_STORE, sha1sum[0:2], sha1sum)

        b = Blob.objects.get(sha1sum=sha1sum)
        file_path = "%s/%s" % (b.get_parent_dir(), b.filename)

        # Is the blob itself an image?
        filename, file_extension = os.path.splitext(b.filename)
        if file_extension[1:] in ['gif', 'jpg', 'png']:
            info = Blob.get_image_dimensions(file_path, max_cover_image_width)
            info['url'] = "blobs/%s/%s/%s" % (sha1sum[0:2], sha1sum, b.filename)

        # Nope. Look for a cover image
        for image_type in ['jpg', 'png']:
            for cover_image in ["cover.%s" % image_type, "cover-%s.%s" % (size, image_type)]:
                file_path = "%s/%s" % (parent_dir, cover_image)
                if os.path.isfile(file_path):
                    info = Blob.get_image_dimensions(file_path, max_cover_image_width)
                    info['url'] = "blobs/%s/%s/%s" % (sha1sum[0:2], sha1sum, cover_image)

        # If we get this far, return the default image
        if not info.get('url'):
            info = {'url': 'images/book.png', 'height_cropped': 128, 'width_cropped': 128}

        return info

    def get_solr_info(self, query, **kwargs):
        conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        solr_args = {'q': query,
                     'wt': 'json',
                     'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,content_type,doctype,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url,bordercore_blogpost_title',
                     'rows': 1000}
        return json.loads(conn.raw_query(**solr_args))['response']

    def get_related_blobs(self):
        related_blobs = []
        for blob in self.blobs.all():
            related_blobs.append({'sha1sum': blob.sha1sum, 'title': blob.metadata_set.filter(name='Title')})
        return related_blobs

    def delete(self):
        file_path = "%s/%s" % (self.get_parent_dir(), self.filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

            self.delete_cover_images()

            # Delete the parent dir if this is not an ebook
            os.rmdir("%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum))
            # If the parent of that is empty, delete it, too
            parent_dir = "%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2])
            if os.listdir(parent_dir) == []:
                os.rmdir(parent_dir)

            # Remove this blob from any collections
            for c in Collection.objects.all():
                c.blob_list = [x for x in c.blob_list if x['id'] != self.id]
                c.save()

            # Delete the blob in Solr
            conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
            conn.delete(queries=['sha1sum:%s' % (self.sha1sum)])
            conn.commit()

            super(Blob, self).delete()
        else:
            raise Exception("File does not exist: %s" % file_path)

    def delete_cover_images(self):
        for file in os.listdir(self.get_parent_dir()):
            filename, file_extension = os.path.splitext(file)
            if file_extension[1:] in ['jpg', 'png']:
                os.remove("%s/%s" % (self.get_parent_dir(), file))

    def get_content_type(self, argument):
        switcher = {
            "application/pdf": "PDF",
            "image/jpeg": "Image",
            "image/png": "Image"
        }

        return switcher.get(argument, lambda: argument)

    def get_collection_info(self):
        return Collection.objects.filter(blob_list__contains=[{'id': self.id}])


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob)

    class Meta:
        unique_together = ('name', 'value', 'blob')
