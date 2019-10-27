import glob
import hashlib
import json
import logging
import os
import os.path
from pathlib import Path
import re
import shutil
import urllib.parse
import uuid

import boto3
import markdown
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch.dispatcher import receiver
from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image
from storages.backends.s3boto3 import S3Boto3Storage

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
BLOB_TMP_DIR = "/tmp/bordercore-blobs"


logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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


class DownloadableS3Boto3Storage(S3Boto3Storage):

    # Override this to prevent Django from cleaning the name (eg replacing spaces with underscores)
    def get_valid_name(self, name):
        return name

    def _save(self, name, content):
        """
        Override _save() to set a custom S3 location for the object
        """

        hasher = hashlib.sha1()
        for chunk in content.chunks():
            hasher.update(chunk)
        sha1sum = hasher.hexdigest()

        self.location = "blobs/{}/{}".format(sha1sum[0:2], sha1sum)
        return super()._save(name, content)


class Document(TimeStampedModel, AmazonMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = models.TextField(null=True)
    title = models.TextField(null=True)
    sha1sum = models.CharField(max_length=40, unique=True, blank=True, null=True)
    file_s3 = models.FileField(max_length=500, storage=DownloadableS3Boto3Storage())
    file = models.FileField(upload_to=blob_directory_path, storage=BlobFileSystemStorage(), max_length=500)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    date = models.TextField(null=True)
    importance = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    is_note = models.BooleanField(default=False)
    documents = models.ManyToManyField("self")

    def get_content(self):
        return markdown.markdown(self.content, extensions=['codehilite(guess_lang=False)', 'tables'])

    def get_note(self):
        return markdown.markdown(self.note, extensions=['codehilite(guess_lang=False)', 'tables'])

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

    def is_pdf(self):
        if self.file:
            _, file_extension = os.path.splitext(str(self.file))
            if file_extension[1:].lower() in ['pdf']:
                return True
        return False

    def get_parent_dir(self):
        return "{}/{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2], self.sha1sum)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_url(self):
        return f"{self.sha1sum[0:2]}/{self.sha1sum}/{self.file_s3}"

    def get_title(self, remove_edition_string=False, use_filename_if_present=False):
        title = self.title
        if title:
            if remove_edition_string:
                pattern = re.compile('(.*) (\d)E$')
                matches = pattern.match(title)
                if matches and EDITIONS[matches.group(2)]:
                    return "%s" % (matches.group(1))
            return title
        else:
            if use_filename_if_present:
                return os.path.basename(str(self.file))
            else:
                return "No title"

    def get_edition_string(self):
        if self.title:
            pattern = re.compile('(.*) (\d)E$')
            matches = pattern.match(self.title)
            if matches and EDITIONS[matches.group(2)]:
                return "%s Edition" % (EDITIONS[matches.group(2)])

        return ""

    def get_s3_key(self):
        if self.file_s3:
            return "{}/{}/{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2], self.sha1sum, self.file_s3)
        else:
            return None

    def get_solr_info(self, query, **kwargs):
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        solr_args = {'q': query,
                     'wt': 'json',
                     'fl': 'author,bordercore_todo_task,content_type,doctype,note,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url',
                     'rows': 1000}
        return json.loads(conn.raw_query(**solr_args).decode('UTF-8'))['response']

    def create_tmp_directory(self, uuid):
        """
        Store newly uploaded files in a tmp directory that looks like this:

        /tmp/bordercore-blobs/<uuid>/<filename>

        This is so a later celery process can send the new file
        to Solr for indexing. This process is also responsible
        for cleaning up these tmp directories.
        """

        dir = Path(f"{BLOB_TMP_DIR}/{uuid}")
        if not dir.is_dir():
            os.umask(0o002)
            dir.mkdir(mode=0o775, parents=True, exist_ok=True)
            return dir
        else:
            log.error("Tmp directory already exists: {dir}")

    def save(self, *args, **kwargs):

        # We rely on the readable() method to determine if we're
        #  adding a new file or editing an existing one. If it's
        #  new, we have access to the file since it was just
        #  uploaded, so calculate the sha1sum. If we're editing the
        #  file, we don't have access to any file, so don't try
        #  to calculate the sha1sum.

        if self.file_s3 and self.file_s3.readable():

            tmp_dir = self.create_tmp_directory(self.uuid)

            # While computing the sha1sum, store the file in a tmp
            # directory for later Solr indexing for a celery process
            with open(f"{tmp_dir}/{self.file_s3}", "wb") as out_file:
                hasher = hashlib.sha1()
                for chunk in self.file_s3.chunks():
                    hasher.update(chunk)
                    out_file.write(chunk)
                self.sha1sum = hasher.hexdigest()

        super(Document, self).save(*args, **kwargs)

    #     if self.file_s3:
    #         old_sha1sum = self.sha1sum
    #         if old_sha1sum is not None:
    #             # We can only move files after super() is called to create the new file's directory structure
    #             # NOTE: the previous comment may not be relevant for storage in S3
    #             if self.sha1sum != old_sha1sum:
    #                 create_thumbnail.delay(self.uuid)
    #                 self.change_file_s3(old_sha1sum)

    def change_file_s3(self, old_sha1sum):

        dir_old = "{}/{}/{}".format(settings.MEDIA_ROOT, old_sha1sum[0:2], old_sha1sum)
        dir_new = self.get_parent_dir()

        # TODO Can we eliminate the client object and just use the s3 object?
        client = boto3.client("s3")
        s3 = boto3.resource("s3")
        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        # Delete the old file.  I don't have access to the old filename at this point,
        #  so instead delete anything that doesn't look like a cover image
        print("dir_old: {}".format(dir_old))
        for fn in my_bucket.objects.filter(Prefix=dir_old):
            print("looking for old key to delete,  fn: {}".format(str(fn.key)))
        # for fn in os.listdir(dir_old):
            if not os.path.basename(str(fn)).startswith("cover-"):
                print ("Deleting key {}".format(fn.key))
                client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key="{}".format(fn.key))
               # os.remove("{}/{}".format(dir_old, fn))

        # Move any cover images for the old file to the new file's directory
        # for file in os.listdir(dir_old):
        #     _, file_extension = os.path.splitext(file)
        #     if file_extension[1:] in ["jpg", "png"]:
        #         pass
        #         # TODO: Implement this in S3
        #         # shutil.move("{}/{}".format(dir_old, file), dir_new)

    def has_been_modified(self):
        """
        If the modified time is greater than the creation time by
        more than one second, assume it has been edited.
        """

        if int(self.modified.strftime("%s")) - int(self.created.strftime("%s")) > 0:
            return True
        else:
            return False

    def get_related_blobs(self):
        related_blobs = []
        for blob in self.documents.all():
            related_blobs.append({'uuid': blob.uuid, 'title': blob.title})
        return related_blobs

    def get_collection_info(self):
        return Collection.objects.filter(user=self.user, blob_list__contains=[{'id': self.id}])

    def has_thumbnail_url(self):
        try:
            _ = Document.get_cover_info_s3(self.user, self.sha1sum, size='small')['url']
            return True
        except:
            return False

    def get_cover_url_small(self):
        return Document.get_cover_info_s3(self.user, self.sha1sum, size='small')['url']

    @staticmethod
    def get_image_dimensions_s3(blob, max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        info = {}

        s3 = boto3.resource("s3")
        obj = s3.Object(bucket_name=settings.AWS_STORAGE_BUCKET_NAME, key=blob.get_s3_key())

        try:

            info["width"] = int(obj.metadata["image-width"])
            info["height"] = int(obj.metadata["image-height"])

            if info["width"] > max_cover_image_width:
                info["height_cropped"] = int(max_cover_image_width * info["height"] / info["width"])
                info["width_cropped"] = max_cover_image_width

        except KeyError as e:
            print(f"Warning: Object has no metadata {e}")

        return info

    @staticmethod
    def get_cover_info_s3(user, sha1sum, size="large", max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        if sha1sum is None:
            return {}

        info = {}

        parent_dir = "{}/{}/{}".format(settings.MEDIA_ROOT, sha1sum[0:2], sha1sum)

        b = Document.objects.get(user=user, sha1sum=sha1sum)

        prefix, filename = os.path.split(b.get_s3_key())

        s3 = boto3.resource("s3")
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        objects = [os.path.split(x.key)[1] for x in list(bucket.objects.filter(Delimiter="/", Prefix=f"{prefix}/"))]

        # Is the blob itself an image?
        _, file_extension = os.path.splitext(b.file_s3.name)
        if file_extension[1:].lower() in ["gif", "jpg", "jpeg", "png"]:
            # If so, look for a thumbnail.  Otherwise return the image itself
            thumbnail_file_path = "{}/{}".format(parent_dir, "cover.jpg")
            if "cover.jpg" in objects:
                info["url"] = f"{prefix}/cover.jpg"
            else:
                info = Document.get_image_dimensions_s3(b, max_cover_image_width)
                info["url"] = b.get_s3_key()

        else:
            # Nope. Look for a cover image
            for image_type in ["jpg", "png"]:
                for cover_image in ["cover.{}".format(image_type), "cover-{}.{}".format(size, image_type)]:
                    if cover_image in objects:
                        info["url"] = f"{prefix}/{cover_image}"

        # If we get this far, return the default image
        if not info.get("url"):
            info = {"url": "django/img/book.png", "height_cropped": 128, "width_cropped": 128}

        info["url"] = urllib.parse.quote(info["url"])
        return info

    def create_thumbnail(self, page_number=1):

        if self.is_image():
            self.create_thumbnail_from_image()
        elif self.is_pdf():
            self.create_thumbnail_from_pdf(page_number)
        self.fix_permissions()

    def create_thumbnail_from_image(self):

        size = 128, 128

        infile = "{}/{}".format(settings.MEDIA_ROOT, self.file.name)
        outfile = "{}/{}/cover-small.jpg".format(settings.MEDIA_ROOT, os.path.dirname(self.file.name))
        try:
            # Convert images to RGB mode to avoid "cannot write mode P as JPEG" errors for PNGs
            im = Image.open(infile).convert('RGB')
            im.thumbnail(size)
            im.save(outfile)
            os.chmod(outfile, 0o664)
        except IOError as err:
            print("cannot create thumbnail; error={}".format(err))

    def create_thumbnail_from_pdf(self, page_number):

        page_number = page_number - 1

        os.chdir("{}/{}".format(settings.MEDIA_ROOT, os.path.dirname(self.file.name)))

        # Ex: d7/d77d08dd2e51680229adbf175101b8f65f3717fc/Comprehensive Report.pdf
        input_file = os.path.basename(self.file.name)

        # Ex: Comprehensive Report_p1.pdf
        outfile = "{}_p{}.pdf".format(os.path.splitext(input_file)[0], page_number)

        input_pdf = PdfFileReader(open(input_file, "rb"))

        # Some documents are recognized as encrypted, even though they're not.
        #  This is a workaround
        if input_pdf.getIsEncrypted():
            input_pdf.decrypt('')

        output = PdfFileWriter()
        output.addPage(input_pdf.getPage(page_number))
        outputStream = open(outfile, "wb")
        output.write(outputStream)
        outputStream.close()

        # Convert the pdf page to jpg
        from pdf2image import convert_from_path
        pages = convert_from_path(outfile, dpi=150)
        cover_large = "cover-large.jpg"
        pages[0].save(cover_large, "JPEG")

        # Create small (thumbnail) jpg
        from PIL import Image

        size = 128, 128

        try:
            im = Image.open(cover_large)
            im.thumbnail(size)
            im.save("cover-small.jpg".format(page_number), "JPEG")
        except IOError:
            print("Cannot create thumbnail for {}".format(cover_large))

        os.remove(outfile)

    def fix_permissions(self):
        """
        Set all cover images to be chmod = 664
        """

        files = "{}/{}/cover-*".format(settings.MEDIA_ROOT,
                                       os.path.dirname(self.file.name))
        for name in glob.glob(files):
            os.chmod(name, 0o664)

    def delete(self):
        # Delete from Solr
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['uuid:{}'.format(self.uuid)])
        conn.commit()

        # Delete from any collections
        for collection in Collection.objects.filter(user=self.user, blob_list__contains=[{'id': self.id}]):
            collection.blob_list = [x for x in collection.blob_list if x['id'] != self.id]
            collection.save()

        super(Document, self).delete()


@receiver(post_save, sender=Document)
def set_s3_metadata_file_modified(sender, instance, **kwargs):
    """
    Store a file's modification time as S3 metadata after it's saved.
    """

    # instance.file_modified will be "None" if we're editing a blob's
    # information, but not changing the blob itself. In that case we
    # don't want to update its "file_modified" metadata.
    if not instance.file_s3 or instance.file_modified is None:
        return

    s3 = boto3.resource("s3")
    key = instance.get_s3_key()

    s3_object = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key)

    s3_object.metadata.update({"file-modified": str(instance.file_modified)})
    s3_object.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}, Metadata=s3_object.metadata, MetadataDirective="REPLACE")


@receiver(pre_delete, sender=Document)
def mymodel_delete_s3(sender, instance, **kwargs):

    if instance.file_s3:

        dir = "{}/{}/{}".format(settings.MEDIA_ROOT, instance.sha1sum[0:2], instance.sha1sum)
        s3 = boto3.resource("s3")
        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        # TODO: Add sanity check to prevent unwanted deletes?
        for fn in my_bucket.objects.filter(Prefix=dir):
            print(f"Deleting blob {fn}")
            fn.delete()

        # Pass false so FileField doesn't save the model.
        instance.file_s3.delete(False)


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('name', 'value', 'blob')

    def delete(self):

        delete_metadata.delay(self.blob.uuid, self.name, self.value)

        super(MetaData, self).delete()
