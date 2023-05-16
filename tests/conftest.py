"""
Pytest Fixtures Shared Across all Unit Tests
"""

import pathlib

import pytest
from click.testing import CliRunner

from browsr import Browsr
from browsr._base import TextualAppContext


@pytest.fixture
def runner() -> CliRunner:
    """
    Return a CliRunner object
    """
    return CliRunner()


@pytest.fixture
def repo_dir() -> pathlib.Path:
    """
    Return the path to the repository root
    """
    return pathlib.Path(__file__).parent.parent.resolve()


@pytest.fixture
def screenshot_dir(repo_dir: pathlib.Path) -> pathlib.Path:
    """
    Return the path to the screenshot directory
    """
    return repo_dir / "tests" / "screenshots"


@pytest.fixture
def app(repo_dir: pathlib.Path) -> Browsr:
    """
    Textual Screenshotting Tests
    """
    context = TextualAppContext(
        file_path=str(repo_dir),
    )
    app = Browsr(config_object=context)
    return app
