import logging
import os
import subprocess
from pathlib import PurePath

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

    # Isolate the import here so other functions from this module
    #  can be imported without requiring these dependencies.
    from pdf2image import convert_from_path
    from PyPDF2 import PdfFileReader, PdfFileWriter

    page_number = page_number - 1

    # Ex: Comprehensive Report_p1.pdf
    outfile = "{}_p{}.pdf".format(PurePath(infile).parent / PurePath(infile).stem, page_number)

    input_pdf = PdfFileReader(open(infile, "rb"))

    # Some documents are recognized as encrypted, even though they're not.
    #  This is a workaround.
    if input_pdf.getIsEncrypted():
        input_pdf.decrypt('')

    output = PdfFileWriter()
    output.addPage(input_pdf.getPage(page_number))
    outputStream = open(outfile, "wb")
    output.write(outputStream)
    outputStream.close()

    # Convert the pdf page to jpg
    pages = convert_from_path(outfile, dpi=150)
    cover_large = f"{outdir}-cover-large.jpg"
    pages[0].save(cover_large, "JPEG")

    create_small_cover_image(cover_large, outdir)

    os.remove(outfile)


def create_thumbnail_from_video(infile, outdir):

    thumbnail_filename = f"{outdir}-cover-large.jpg"

    # ffmpeg -ss 00:00:10  -i Fix*mp4 -vframes 1 -q:v 2 output.jpg

    result = subprocess.run(
        [
            "ffmpeg",
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
