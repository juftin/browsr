"""
Pytest Fixtures Shared Across all Unit Tests
"""

import pathlib
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner
from textual_universal_directorytree import GitHubPath


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
def github_release_path() -> GitHubPath:
    """
    Return the path to the Github Release
    """
    release = "v1.6.0"
    uri = f"github://juftin:browsr@{release}"
    return GitHubPath(uri)


@pytest.fixture(scope="module")
def vcr_config() -> Dict[str, List[Any]]:
    """
    VCR Cassette Privacy Enforcer

    This fixture ensures the API Credentials are obfuscated

    Returns
    -------
    Dict[str, list]:
    """
    return {
        "filter_headers": [("authorization", "XXXXXXXXXX")],
        "filter_query_parameters": [("user", "XXXXXXXXXX"), ("token", "XXXXXXXXXX")],
    }


cassette = pytest.mark.vcr(scope="module")
