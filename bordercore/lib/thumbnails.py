import logging
import os
from pathlib import PurePath

from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter

from .util import is_image, is_pdf

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def create_thumbnail(infile, outdir):

    if is_image(infile):
        create_thumbnail_from_image(infile, outdir)
    elif is_pdf(infile):
        create_thumbnail_from_pdf(infile, outdir, 1)
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

    # Resize the large cover jpg to create a small (thumbnail) jpg

    size = 128, 128

    try:
        im = Image.open(cover_large)
        im.thumbnail(size)
        im.save(f"{outdir}-cover-small.jpg", "JPEG")
    except IOError:
        print(f"Cannot create small thumbnail for {cover_large}")

    os.remove(outfile)
