"""
Code Browsr Utility Functions
"""

import datetime
import os
import pathlib
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, Union

import fitz  # type: ignore[import]
import rich_pixels
from fitz import Pixmap
from PIL import Image
from rich_pixels import Pixels
from upath.implementations.cloud import CloudPath


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


@dataclass
class FileInfo:
    """
    File Information Object
    """

    file: pathlib.Path
    size: int
    last_modified: datetime.datetime
    stat: Union[Dict[str, Any], os.stat_result]
    is_local: bool
    is_file: bool
    owner: str
    group: str
    is_cloudpath: bool


def get_file_info(file_path: pathlib.Path) -> FileInfo:
    """
    Get File Information, Regardless of the FileSystem
    """
    stat = file_path.stat()
    is_file = file_path.is_file()
    is_cloudpath = isinstance(file_path, CloudPath)
    if isinstance(stat, dict):
        # raise ValueError(json.dumps(stat, indent=4))
        lower_dict = {key.lower(): value for key, value in stat.items()}
        file_size = lower_dict["size"]
        last_modified = lower_dict.get("lastmodified") or lower_dict.get("updated")
        if isinstance(last_modified, str):
            # 2023-05-12T21:25:17.050Z
            last_modified = datetime.datetime.fromisoformat(last_modified[:-1])
        return FileInfo(
            file=file_path,
            size=file_size,
            last_modified=last_modified,
            stat=stat,
            is_local=False,
            is_file=is_file,
            owner="",
            group="",
            is_cloudpath=is_cloudpath,
        )
    else:
        last_modified = datetime.datetime.fromtimestamp(stat.st_mtime)
        return FileInfo(
            file=file_path,
            size=stat.st_size,
            last_modified=last_modified,
            stat=stat,
            is_local=True,
            is_file=is_file,
            owner=file_path.owner(),
            group=file_path.group(),
            is_cloudpath=is_cloudpath,
        )


def handle_duplicate_filenames(file_path: pathlib.Path) -> pathlib.Path:
    """
    Handle Duplicate Filenames

    Duplicate filenames are handled by appending a number to the filename
    in the form of "filename (1).ext", "filename (2).ext", etc.
    """
    if not file_path.exists():
        return file_path
    else:
        i = 1
        while True:
            new_file_stem = f"{file_path.stem} ({i})"
            new_file_path = file_path.with_stem(new_file_stem)
            if not new_file_path.exists():
                return new_file_path
            i += 1
