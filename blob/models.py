import os

from django.contrib.auth.models import User
from django.db import models
from lib.mixins import TimeStampedModel

from tag.models import Tag

class Blob(TimeStampedModel):
    """
    A blob belonging to a user.
    """
    EBOOK_DIR = '/home/media/ebooks'
    BLOB_STORE = '/home/media/blobs'

    sha1sum = models.CharField(max_length=40, unique=True)
    filename = models.TextField()
    file_path = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_parent_dir(self):
        return "%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum)

    def get_title(self):
        m = self.metadata_set.filter(name='Title')
        if m:
            return m[0].value
        else:
            return "No title"

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


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob)

    class Meta:
        unique_together = ('name', 'value', 'blob')

