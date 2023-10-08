import logging
import subprocess

from PIL import Image

from .util import is_image, is_pdf, is_video

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def create_thumbnail(infile, outdir, page_number=1):

    if is_image(infile):
        create_thumbnail_from_image(infile, outdir)
    elif is_pdf(infile):
        create_thumbnail_from_pdf(infile, outdir, page_number)
    elif is_video(infile):
        create_thumbnail_from_video(infile, outdir)
    else:
        log.warn("Can't create thumbnail from this type of file")


def create_thumbnail_from_image(infile, outdir):

    size = 128, 128

    try:
        # Convert images to RGB mode to avoid "cannot write mode P as JPEG" errors for PNGs
        im = Image.open(infile).convert("RGB")
        im.thumbnail(size)
        im.save(f"{outdir}-cover.jpg")
    except IOError as err:
        log.error(f"Cannot create thumbnail; error={err}")


def create_thumbnail_from_pdf(infile, outdir, page_number=1):

    # Put the import here so that AWS lambdas that use other functions in this
    # module don't need to install the PyMuPDF package, which provides fitz
    import fitz

    page_number = page_number - 1
    cover_large = f"{outdir}-cover-large.jpg"

    doc = fitz.open(infile)
    page = doc.load_page(page_number)
    pix = page.get_pixmap(dpi=150)
    pix.pil_save(cover_large)

    create_small_cover_image(cover_large, outdir)


def create_thumbnail_from_video(infile, outdir):

    thumbnail_filename = f"{outdir}-cover-large.jpg"

    # ffmpeg -ss 00:00:10  -i Fix*mp4 -vframes 1 -q:v 2 output.jpg

    subprocess.run(
        [
            "/usr/local/bin/ffmpeg",
            "-ss",
            "00:00:01",
            "-i",
            infile,
            "-vframes",
            "1",
            "-q:v",
            "2",
            thumbnail_filename
        ]
    )

    create_small_cover_image(thumbnail_filename, outdir)


def create_small_cover_image(cover_large, outdir):
    """
    Resize the large cover jpg to create a small (thumbnail) jpg
    """

    size = 128, 128

    try:
        im = Image.open(cover_large)
        im.thumbnail(size)
        im.save(f"{outdir}-cover.jpg", "JPEG")
    except IOError:
        print(f"Cannot create small thumbnail for {cover_large}")


def create_bookmark_thumbnail(cover_large, out_file):
    """
    Resize the large cover png to create a small (thumbnail) png
    """

    size = 128, 128

    try:
        im = Image.open(cover_large)
        im.thumbnail(size)
        im.save(out_file, "PNG")
    except IOError:
        print(f"Cannot create thumbnail for {cover_large}")
