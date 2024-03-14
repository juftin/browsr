"""
Screenshot Testing Using Cassettes!
"""

from textwrap import dedent
from typing import Callable, Tuple

import pytest
from textual_universal_directorytree import GitHubTextualPath, UPath

from tests.conftest import cassette


@pytest.fixture
def app_file() -> str:
    file_content = """
    from browsr.browsr import Browsr
    from browsr.base import TextualAppContext

    file_path = "{file_path}"
    context = TextualAppContext(file_path=file_path)
    app = Browsr(config_object=context)
    """
    return dedent(file_content).strip()


@pytest.fixture
def terminal_size() -> Tuple[int, int]:
    return 160, 48


@cassette
def test_github_screenshot(
    snap_compare: Callable[..., bool],
    tmp_path: UPath,
    app_file: str,
    github_release_path: GitHubTextualPath,
    terminal_size: Tuple[int, int],
) -> None:
    """
    Snapshot a release of this repo
    """
    app_path = tmp_path / "app.py"
    app_path.write_text(app_file.format(file_path=str(github_release_path)))
    assert snap_compare(app_path=app_path, terminal_size=terminal_size)


@cassette
def test_github_screenshot_license(
    snap_compare: Callable[..., bool],
    tmp_path: UPath,
    app_file: str,
    github_release_path: GitHubTextualPath,
    terminal_size: Tuple[int, int],
) -> None:
    """
    Snapshot the LICENSE file
    """
    file_path = str(github_release_path / "LICENSE")
    app_path = tmp_path / "app.py"
    app_path.write_text(app_file.format(file_path=file_path))
    assert snap_compare(app_path=app_path, terminal_size=terminal_size)


@cassette
def test_mkdocs_screenshot(
    snap_compare: Callable[..., bool],
    tmp_path: UPath,
    app_file: str,
    terminal_size: Tuple[int, int],
    github_release_path: GitHubTextualPath,
) -> None:
    """
    Snapshot the pyproject.toml file
    """
    file_path = str(github_release_path / "mkdocs.yaml")
    app_path = tmp_path / "app.py"
    app_path.write_text(app_file.format(file_path=file_path))
    assert snap_compare(app_path=app_path, terminal_size=terminal_size)
