"""
Screenshot Testing Using Cassettes!
"""

from textual_universal_directorytree import GitHubPath

from tests.conftest import cassette
from tests.helpers import Screenshotter


@cassette
def test_github_screenshot(github_release_path: GitHubPath) -> None:
    """
    Snapshot a release of this repo
    """
    file_path = str(github_release_path)
    screenshotter = Screenshotter(file_path=file_path)
    screenshot, screenshot_path = screenshotter.take_screenshot()
    assert screenshot_path.read_text() == screenshot


@cassette
def test_github_screenshot_license(github_release_path: GitHubPath) -> None:
    """
    Snapshot the LICENSE file
    """
    file_path = str(github_release_path / "LICENSE")
    screenshotter = Screenshotter(file_path=file_path)
    screenshot, screenshot_path = screenshotter.take_screenshot()
    assert screenshot_path.read_text() == screenshot
