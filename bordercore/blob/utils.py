import os.path

from django.conf import settings

from blob.models import Document

MAX_COVER_IMAGE_WIDTH = 800

def get_cover_info(sha1sum, size='large', max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

    info = {}

    if sha1sum is None:
        return {}

    # parent_dir = "%s/%s/%s" % (settings.MEDIA_ROOT, sha1sum[0:2], sha1sum)

    b = Document.objects.get(sha1sum=sha1sum)
    parent_dir = b.get_parent_dir()
    # file_path = "%s/%s" % (b.get_parent_dir(), b.filename)
    file_path = "{}/{}".format(settings.MEDIA_ROOT, b.file.name)

    # Is the blob itself an image?
    filename, file_extension = os.path.splitext(b.file.name)
    if file_extension[1:] in ['gif', 'jpg', 'jpeg', 'png']:
        info = Document.get_image_dimensions(file_path, max_cover_image_width)
        # info['url'] = "blobs/%s/%s/%s" % (sha1sum[0:2], sha1sum, b.filename)
        info['url'] = "blobs/{}".format(b.file.name)

    # Nope. Look for a cover image
    for image_type in ['jpg', 'png']:
        for cover_image in ["cover.%s" % image_type, "cover-%s.%s" % (size, image_type)]:
            file_path = "%s/%s" % (parent_dir, cover_image)
            if os.path.isfile(file_path):
                info = Document.get_image_dimensions(file_path, max_cover_image_width)
                info['url'] = "blobs/%s/%s/%s" % (sha1sum[0:2], sha1sum, cover_image)

    # If we get this far, return the default image
    if not info.get('url'):
        info = {'url': 'images/book.png', 'height_cropped': 128, 'width_cropped': 128}

    return info
