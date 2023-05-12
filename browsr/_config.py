"""
browsr configuration file
"""

from os import getenv
from typing import List

favorite_themes: List[str] = [
    "monokai",
    "material",
    "dracula",
    "solarized-light",
    "one-dark",
    "solarized-dark",
    "emacs",
    "vim",
    "github-dark",
    "native",
    "paraiso-dark",
]
rich_default_theme = getenv("RICH_THEME", None)

if rich_default_theme in favorite_themes:
    assert isinstance(rich_default_theme, str)
    favorite_themes.remove(rich_default_theme)
if rich_default_theme is not None:
    assert isinstance(rich_default_theme, str)
    favorite_themes.insert(0, rich_default_theme)

image_file_extensions = [
    ".bmp",
    ".dib",
    ".eps",
    ".ps",
    ".gif",
    ".icns",
    ".ico",
    ".cur",
    ".im",
    ".im.gz",
    ".im.bz2",
    ".jpg",
    ".jpe",
    ".jpeg",
    ".jfif",
    ".msp",
    ".pcx",
    ".png",
    ".ppm",
    ".pbm",
    ".pgm",
    ".sgi",
    ".rgb",
    ".bw",
    ".spi",
    ".tif",
    ".tiff",
    ".webp",
    ".xbm",
    ".xv",
    ".pdf",
]
