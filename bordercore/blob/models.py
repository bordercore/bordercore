import hashlib
import json
import os
import os.path
import re
import shutil
import uuid

import markdown
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from PIL import Image

from blob.amazon import AmazonMixin
from blob.tasks import create_thumbnail, delete_metadata
from collection.models import Collection
from lib.mixins import TimeStampedModel
from solrpy.core import SolrConnection
from tag.models import Tag

EDITIONS = {'1': 'First',
            '2': 'Second',
            '3': 'Third',
            '4': 'Fourth',
            '5': 'Fifth',
            '6': 'Sixth',
            '7': 'Seventh',
            '8': 'Eighth'}

MAX_COVER_IMAGE_WIDTH = 800


# Override FileSystemStorage to get better control of how files are named
class BlobFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise(Exception("name's length is greater than max_length"))
        return name

    # Override this to prevent Django from cleaning the name (eg replacing spaces with underscores)
    def get_valid_name(self, name):
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(BlobFileSystemStorage, self)._save(name, content)


def blob_directory_path(instance, filename):

    hasher = hashlib.sha1()
    for chunk in instance.file.chunks():
        hasher.update(chunk)

    sha1sum = hasher.hexdigest()

    dir = "{}/{}/{}".format(settings.MEDIA_ROOT, sha1sum[0:2], sha1sum)
    if not os.path.exists(dir):
        os.makedirs(dir)
        os.chmod(dir, 0o2775)
    filepath = "{}/{}/{}".format(sha1sum[0:2], sha1sum, filename)

    return filepath


class Document(TimeStampedModel, AmazonMixin):
    """
    The base class
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = models.TextField(null=True)
    title = models.TextField(null=True)
    sha1sum = models.CharField(max_length=40, unique=True, blank=True, null=True)
    file = models.FileField(upload_to=blob_directory_path, storage=BlobFileSystemStorage(), max_length=500)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    date = models.TextField(null=True)
    importance = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    is_blog = models.BooleanField(default=False)
    documents = models.ManyToManyField("self")

    def get_content(self):
        return markdown.markdown(self.content, extensions=['codehilite(guess_lang=False)'])

    @staticmethod
    def get_content_type(argument):
        switcher = {
            "application/mp4": "Video",
            "application/pdf": "PDF",
            "audio/mpeg": "Audio",
            "image/gif": "Image",
            "image/jpeg": "Image",
            "image/png": "Image",
            "application/x-mobipocket-ebook": "E-Book",
        }

        return switcher.get(argument, "")

    def is_image(self):
        if self.file:
            _, file_extension = os.path.splitext(str(self.file))
            if file_extension[1:].lower() in ['gif', 'jpg', 'jpeg', 'png']:
                return True
        return False

    def get_parent_dir(self):
        return "{}/{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2], self.sha1sum)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_url(self):
        return self.file

    def get_title(self, remove_edition_string=False):
        title = self.title
        if title:
            if remove_edition_string:
                pattern = re.compile('(.*) (\d)E$')
                matches = pattern.match(title)
                if matches and EDITIONS[matches.group(2)]:
                    return "%s" % (matches.group(1))
            return title
        else:
            return "No title"

    def get_edition_string(self):
        if self.title:
            pattern = re.compile('(.*) (\d)E$')
            matches = pattern.match(self.title)
            if matches and EDITIONS[matches.group(2)]:
                return "%s Edition" % (EDITIONS[matches.group(2)])

        return ""

    def get_solr_info(self, query, **kwargs):
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        solr_args = {'q': query,
                     'wt': 'json',
                     'fl': 'author,bordercore_todo_task,content_type,doctype,note,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url,bordercore_blogpost_title',
                     'rows': 1000}
        return json.loads(conn.raw_query(**solr_args).decode('UTF-8'))['response']

    def save(self, *args, **kwargs):
        if self.file:
            old_sha1sum = self.sha1sum
            hasher = hashlib.sha1()
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.sha1sum = hasher.hexdigest()
        super(Document, self).save(*args, **kwargs)

        if self.file and old_sha1sum is not None:
            # We can only move files after super() is called to create the new file's directory structure
            if self.sha1sum != old_sha1sum:
                create_thumbnail.delay(self.uuid)
                self.change_file(old_sha1sum)
        else:
            # This is a new file.  Attempt to create a thumbnail.
            create_thumbnail.delay(self.uuid)

    def change_file(self, old_sha1sum):

        dir_old = "{}/{}/{}".format(settings.MEDIA_ROOT, old_sha1sum[0:2], old_sha1sum)
        dir_new = self.get_parent_dir()

        # Delete the old file.  I don't have access to the old filename at this point,
        #  so instead delete anything that doesn't look like a cover image
        for fn in os.listdir(dir_old):
            if not os.path.basename(fn).startswith('cover-'):
                print ("Deleting {}/{}".format(dir_old, fn))
                os.remove("{}/{}".format(dir_old, fn))

        # Move any cover images for the old file to the new file's directory
        for file in os.listdir(dir_old):
            _, file_extension = os.path.splitext(file)
            if file_extension[1:] in ['jpg', 'png']:
                shutil.move("{}/{}".format(dir_old, file), dir_new)

        # Delete the old file's directory.  It should be empty at this point.
        os.rmdir(dir_old)

        # If the parent of that is also empty, delete it, too
        parent_dir = "{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2])
        if os.listdir(parent_dir) == []:
            print("Deleting empty parent dir: {}".format(parent_dir))
            os.rmdir(parent_dir)

    def get_related_blobs(self):
        related_blobs = []
        for blob in self.documents.all():
            related_blobs.append({'uuid': blob.uuid, 'title': blob.title})
        return related_blobs

    def get_collection_info(self):
        return Collection.objects.filter(blob_list__contains=[{'id': self.id}])

    def has_thumbnail_url(self):
        try:
            _ = Document.get_cover_info(self.sha1sum, size='small')['url']
            return True
        except:
            return False

    def get_cover_url_small(self):
        return Document.get_cover_info(self.sha1sum, size='small')['url']

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

        if sha1sum is None:
            return {}

        info = {}

        parent_dir = "{}/{}/{}".format(settings.MEDIA_ROOT, sha1sum[0:2], sha1sum)

        b = Document.objects.get(sha1sum=sha1sum)
        file_path = "{}/{}".format(settings.MEDIA_ROOT, b.file.name)

        # Is the blob itself an image?
        _, file_extension = os.path.splitext(file_path)
        if file_extension[1:].lower() in ['gif', 'jpg', 'jpeg', 'png']:
            # If so, look for a thumbnail.  Otherwise return the image itself
            if size == 'small':
                thumbnail_file_path = "{}/{}".format(parent_dir, "cover-small.jpg")
                if os.path.isfile(thumbnail_file_path):
                    file_path = thumbnail_file_path
                    url_path = "{}/{}/{}".format(sha1sum[0:2], sha1sum, "cover-small.jpg")
                    info['url'] = "blobs/{}".format(url_path)
            else:
                # url_path = b.file.name
                # info['url'] = "blobs/{}".format(url_path)
                info = Document.get_image_dimensions(file_path, max_cover_image_width)
                info['url'] = "blobs/{}".format(b.file.name)

        # Nope. Look for a cover image
        for image_type in ['jpg', 'png']:
            for cover_image in ["cover.{}".format(image_type), "cover-{}.{}".format(size, image_type)]:
                file_path = "{}/{}".format(parent_dir, cover_image)
                if os.path.isfile(file_path):
                    info = Document.get_image_dimensions(file_path, max_cover_image_width)
                    info['url'] = "blobs/{}/{}/{}".format(sha1sum[0:2], sha1sum, cover_image)

        # If we get this far, return the default image
        if not info.get('url'):
            info = {'url': 'images/book.png', 'height_cropped': 128, 'width_cropped': 128}

        return info

    def delete(self):
        # Delete from Solr
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['uuid:{}'.format(self.uuid)])
        conn.commit()

        # Delete from any collections
        for collection in Collection.objects.filter(blob_list__contains=[{'id': self.id}]):
            collection.blob_list = [x for x in collection.blob_list if x['id'] != self.id]
            collection.save()

        super(Document, self).delete()


@receiver(pre_delete, sender=Document)
def mymodel_delete(sender, instance, **kwargs):

    if instance.file:
        dir = instance.get_parent_dir()
        for fn in os.listdir(dir):
            print ("Deleting {}/{}".format(dir, fn))
            os.remove("{}/{}".format(dir, fn))

        # Delete the old file's directory.  It should be empty at this point.
        os.rmdir(dir)

        # If the parent of that is also empty, delete it, too
        parent_dir = "{}/{}".format(settings.MEDIA_ROOT, instance.sha1sum[0:2])
        if os.listdir(parent_dir) == []:
            print("Deleting empty parent dir: {}".format(parent_dir))
            os.rmdir(parent_dir)

        # Pass false so FileField doesn't save the model.
        instance.file.delete(False)


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Document, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'value', 'blob')

    def delete(self):

        delete_metadata.delay(self.blob.uuid, self.name, self.value)

        super(MetaData, self).delete()
