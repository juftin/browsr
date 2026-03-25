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
    favorite_themes.remove(rich_default_theme)
if rich_default_theme is not None:
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

textarea_default_theme = "vscode_dark"

textarea_theme_map = {
    "monokai": "monokai",
    "dracula": "dracula",
    "github-dark": "vscode_dark",
    "solarized-light": "github_light",
    "material": "vscode_dark",
    "one-dark": "vscode_dark",
    "solarized-dark": "vscode_dark",
    "native": "vscode_dark",
    "emacs": "vscode_dark",
    "vim": "vscode_dark",
    "paraiso-dark": "vscode_dark",
}

language_map = {
    "py": "python",
    "pyi": "python",
    "pyw": "python",
    "md": "markdown",
    "markdown": "markdown",
    "json": "json",
    "toml": "toml",
    "yaml": "yaml",
    "yml": "yaml",
    "html": "html",
    "htm": "html",
    "css": "css",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "rs": "rust",
    "go": "go",
    "sql": "sql",
    "java": "java",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "xml": "xml",
    "rss": "xml",
    "svg": "xml",
    "xsd": "xml",
    "xslt": "xml",
}

filename_map = {
    "uv.lock": "toml",
    "pyproject.toml": "toml",
    "cargo.lock": "toml",
    "cargo.toml": "toml",
    "makefile": "bash",
    "dockerfile": "bash",
    "procfile": "yaml",
    ".gitignore": "bash",
    ".env": "bash",
}
