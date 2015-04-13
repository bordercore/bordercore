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
    file_path = models.TextField()
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_parent_dir(self):
        if self.file_path.startswith(self.BLOB_STORE):
            return "%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum)
        else:
            return self.EBOOK_DIR

    def get_title(self):
        m = self.metadata_set.filter(name='Title')
        if m:
            return m[0].value
        else:
            return "No title"

    def delete(self):
        if os.path.isfile(self.file_path):
            os.remove(self.file_path)
            # Delete the parent dir if this is not an ebook
            if self.file_path.startswith(self.BLOB_STORE):
                os.rmdir("%s/%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2], self.sha1sum))
                # If the parent of that is empty, delete it, too
                parent_dir = "%s/%s" % (self.BLOB_STORE, self.sha1sum[0:2])
                if os.listdir(parent_dir) == []:
                    os.rmdir(parent_dir)
            super(Blob, self).delete()
        else:
            raise Exception("File does not exist: %s" % self.file_path)


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob)

    class Meta:
        unique_together = ('name', 'value', 'blob')

