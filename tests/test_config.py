"""
Config / Context Tests
"""
import pathlib
from dataclasses import is_dataclass

from textual_universal_directorytree import GitHubPath

from browsr._base import TextualAppContext
from browsr._config import favorite_themes
from tests.conftest import cassette


def test_favorite_themes() -> None:
    """
    Test that favorite_themes is a list of strings
    """
    assert isinstance(favorite_themes, list)
    for theme in favorite_themes:
        assert isinstance(theme, str)


def test_textual_app_context() -> None:
    """
    Test that TextualAppContext is a dataclass
    """
    assert is_dataclass(TextualAppContext)


def test_textual_app_context_path() -> None:
    """
    Test that default TextualAppContext.path is CWD
    """
    context = TextualAppContext()
    assert isinstance(context.path, pathlib.Path)
    assert context.path == pathlib.Path.cwd().resolve()


@cassette
def test_textual_app_context_path_github() -> None:
    """
    Test GitHub URL Parsing
    """
    github_strings = [
        "https://github.com/juftin/browsr",
        "https://github.com/juftin/browsr.git",
        "github.com/juftin/browsr",
        "www.github.com/juftin/browsr",
        "https://www.github.com/juftin/browsr",
        "github://juftin:browsr",
        "github://juftin:browsr@main",
    ]
    for _github_string in github_strings:
        context = TextualAppContext(file_path=_github_string)
        handled_github_url = context.path
        expected_file_path = "github://juftin:browsr@main/"
        assert handled_github_url == GitHubPath(expected_file_path)
        assert str(handled_github_url) == expected_file_path
