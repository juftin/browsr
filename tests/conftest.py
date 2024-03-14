"""
Pytest Fixtures Shared Across all Unit Tests
"""

from typing import Any, Dict, List

import pyperclip
import pytest
from click.testing import CliRunner
from textual_universal_directorytree import GitHubTextualPath, UPath


@pytest.fixture
def runner() -> CliRunner:
    """
    Return a CliRunner object
    """
    return CliRunner()


@pytest.fixture
def repo_dir() -> UPath:
    """
    Return the path to the repository root
    """
    return UPath(__file__).parent.parent.resolve()


@pytest.fixture
def screenshot_dir(repo_dir: UPath) -> UPath:
    """
    Return the path to the screenshot directory
    """
    return repo_dir / "tests" / "screenshots"


@pytest.fixture
def github_release_path() -> GitHubTextualPath:
    """
    Return the path to the Github Release
    """
    release = "v1.6.0"
    uri = f"github://juftin:browsr@{release}"
    return GitHubTextualPath(uri)


@pytest.fixture(autouse=True)
def copy_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Override _copy_supported
    """
    monkeypatch.setattr(
        pyperclip, "determine_clipboard", lambda: (lambda: True, lambda: True)
    )


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
