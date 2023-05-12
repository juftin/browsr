"""
Code Browsr Utility Functions
"""

import pathlib
from typing import BinaryIO

import fitz  # type: ignore[import]
import rich_pixels
from fitz import Pixmap
from PIL import Image
from rich_pixels import Pixels


def _open_pdf_as_image(buf: BinaryIO) -> Image.Image:
    """
    Open a PDF file and return a PIL.Image object
    """
    doc = fitz.open(stream=buf.read(), filetype="pdf")
    pix: Pixmap = doc[0].get_pixmap()
    if pix.colorspace is None:
        mode = "L"
    elif pix.colorspace.n == 1:  # PLR2004
        mode = "L" if pix.alpha == 0 else "LA"
    elif pix.colorspace.n == 3:  # noqa PLR2004
        mode = "RGB" if pix.alpha == 0 else "RGBA"
    else:
        mode = "CMYK"
    return Image.frombytes(size=(pix.width, pix.height), data=pix.samples, mode=mode)


def open_image(document: pathlib.Path, screen_width: float) -> Pixels:
    """
    Open an image file and return a rich_pixels.Pixels object
    """
    with document.open("rb") as buf:
        if document.suffix.lower() == ".pdf":
            image = _open_pdf_as_image(buf=buf)
        else:
            image = Image.open(buf)
        image_width = image.width
        image_height = image.height
        size_ratio = image_width / screen_width
        new_width = min(int(image_width / size_ratio), image_width)
        new_height = min(int(image_height / size_ratio), image_height)
        resized = image.resize((new_width, new_height))
        return rich_pixels.Pixels.from_image(resized)
