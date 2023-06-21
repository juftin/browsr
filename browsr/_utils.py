"""
Code Browsr Utility Functions
"""

import datetime
import os
import pathlib
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, Optional, Union

import fitz  # type: ignore[import]
import rich_pixels
from fitz import Pixmap
from PIL import Image
from rich_pixels import Pixels
from textual_universal_directorytree import is_remote_path


def _open_pdf_as_image(buf: BinaryIO) -> Image.Image:
    """
    Open a PDF file and return a PIL.Image object
    """
    doc = fitz.open(stream=buf.read(), filetype="pdf")
    pix: Pixmap = doc[0].get_pixmap()
    if pix.colorspace is None:
        mode = "L"
    elif pix.colorspace.n == 1:
        mode = "L" if pix.alpha == 0 else "LA"
    elif pix.colorspace.n == 3:  # noqa: PLR2004
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
    last_modified: Optional[datetime.datetime]
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
    try:
        stat: Union[Dict[str, Any], os.stat_result] = file_path.stat()
        is_file = file_path.is_file()
    except PermissionError:
        stat = {"size": 0}
        is_file = True
    is_cloudpath = is_remote_path(file_path)
    if isinstance(stat, dict):
        lower_dict = {key.lower(): value for key, value in stat.items()}
        file_size = lower_dict["size"]
        modified_keys = ["lastmodified", "updated", "mtime"]
        last_modified = None
        for modified_key in modified_keys:
            if modified_key in lower_dict:
                last_modified = lower_dict[modified_key]
                break
        if isinstance(last_modified, str):
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
        try:
            owner = file_path.owner()
            group = file_path.group()
        except NotImplementedError:
            owner = ""
            group = ""
        return FileInfo(
            file=file_path,
            size=stat.st_size,
            last_modified=last_modified,
            stat=stat,
            is_local=True,
            is_file=is_file,
            owner=owner,
            group=group,
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


def handle_github_url(url: str) -> str:
    """
    Handle GitHub URLs

    GitHub URLs are handled by converting them to the raw URL.
    """
    try:
        import requests
    except ImportError as e:
        raise ImportError(
            "The requests library is required to browse GitHub files. "
            "Install browsr with the `remote` extra to install requests."
        ) from e

    gitub_prefix = "github://"
    if gitub_prefix in url and "@" not in url:
        _, user_password = url.split("github://")
        org, repo_str = user_password.split(":")
        repo, *args = repo_str.split("/")
    elif gitub_prefix in url and "@" in url:
        return url
    elif "github.com" in url.lower():
        _, org, repo, *args = url.split("/")
    else:
        raise ValueError(f"Invalid GitHub URL: {url}")
    token = os.getenv("GITHUB_TOKEN")
    auth = {"auth": ("Bearer", token)} if token is not None else {}
    resp = requests.get(
        f"https://api.github.com/repos/{org}/{repo}",
        headers={"Accept": "application/vnd.github.v3+json"},
        **auth,  # type: ignore[arg-type]
    )
    resp.raise_for_status()
    default_branch = resp.json()["default_branch"]
    arg_str = "/".join(args)
    github_uri = f"{gitub_prefix}{org}:{repo}@{default_branch}/{arg_str}".rstrip("/")
    return github_uri


class ArchiveFileError(Exception):
    """
    Archive File Error
    """


def render_file_to_string(file_info: FileInfo) -> str:
    """
    Render File to String

    Parameters
    ----------
    file_info : FileInfo
        The file to render.

    Returns
    -------
    str
        The rendered file as a string.
    """
    try:
        return file_info.file.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        if file_info.file.suffix.lower() in [".tar", ".gz", ".zip", ".tgz"]:
            raise ArchiveFileError(
                f"Cannot render archive file {file_info.file}."
            ) from e
        else:
            raise e
