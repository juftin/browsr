"""
Screenshot Testing Using Cassettes!
"""
import pathlib
from os import environ

import pytest
from textual_universal_directorytree import GitHubPath

from browsr import Browsr
from browsr._base import TextualAppContext
from tests.conftest import cassette


@pytest.mark.asyncio
@cassette
async def test_github_screenshot(github_release_path_str: str) -> None:
    """
    Snapshot a release of this repo
    """
    test_dir = pathlib.Path(__file__).parent
    screenshot_dir = test_dir / "screenshots"
    current_test = environ["PYTEST_CURRENT_TEST"].split("::")[-1].split(" ")[0]
    screenshot_path = screenshot_dir / f"{current_test}.svg"
    existing_screenshot_text = screenshot_path.read_text()
    context = TextualAppContext(file_path=github_release_path_str)
    app = Browsr(config_object=context)
    async with app.run_test(size=(160, 48)):
        app.save_screenshot(filename=screenshot_path.name, path=screenshot_path.parent)
    assert existing_screenshot_text == screenshot_path.read_text()


@pytest.mark.asyncio
@cassette
async def test_github_screenshot_license(github_release_path: GitHubPath) -> None:
    """
    Snapshot the LICENSE file
    """
    test_dir = pathlib.Path(__file__).parent
    screenshot_dir = test_dir / "screenshots"
    current_test = environ["PYTEST_CURRENT_TEST"].split("::")[-1].split(" ")[0]
    screenshot_path = screenshot_dir / f"{current_test}.svg"
    existing_screenshot_text = screenshot_path.read_text()
    file_path = str(github_release_path / "LICENSE")
    context = TextualAppContext(file_path=file_path)
    app = Browsr(config_object=context)
    async with app.run_test(size=(160, 48)):
        app.save_screenshot(filename=screenshot_path.name, path=screenshot_path.parent)
    assert existing_screenshot_text == screenshot_path.read_text()
