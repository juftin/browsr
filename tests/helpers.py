"""
Helpers for the tests
"""

import pathlib
from os import environ, getenv
from typing import List, Optional, Tuple

from browsr import Browsr
from browsr._base import TextualAppContext
from browsr._tools import take_screenshot


class Screenshotter:
    """
    App Screenshotter
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize the Screenshotter
        """
        self.screenshot_dir = file_path
        self.context = TextualAppContext(
            file_path=self.screenshot_dir,
        )
        self.app = Browsr(config_object=self.context)

    def take_screenshot(
        self, press: Optional[List[str]] = None
    ) -> Tuple[str, pathlib.Path]:
        """
        Take a Screenshot
        """
        screenshot = take_screenshot(app=self.app, press=press)
        screenshot_path = self._get_screenshot_path()
        if getenv("BROWSR_REGENERATE_SCREENSHOTS", "0") != "0":
            screenshot_path.write_text(screenshot)
        return screenshot, screenshot_path

    @classmethod
    def _get_screenshot_path(cls) -> pathlib.Path:
        """
        Get the Screenshot Path
        """
        test_dir = pathlib.Path(__file__).parent
        screenshot_dir = test_dir / "screenshots"
        current_test = environ["PYTEST_CURRENT_TEST"].split("::")[-1].split(" ")[0]
        screenshot_path = screenshot_dir / f"{current_test}.svg"
        return screenshot_path
