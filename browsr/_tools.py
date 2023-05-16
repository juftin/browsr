"""
Tools for browsr
"""

import pathlib
from typing import List, Optional

from textual._doc import take_svg_screenshot

from browsr import Browsr
from browsr._base import TextualAppContext


def take_screenshot(
    app: Optional[Browsr] = None,
    press: Optional[List[str]] = None,
    file_path: Optional[pathlib.Path] = None,
) -> str:
    """
    Take a screenshot of the app

    Parameters
    ----------
    app: Optional[Browsr]
        The browsr app, if None, a new one will be created
    press: Optional[List[str]]
        A list of keys to press
    file_path: Optional[pathlib.Path]
        The path to open in the app

    Returns
    -------
    str
        The SVG screenshot
    """
    if file_path is None:
        repo_dir = pathlib.Path(__file__).parent.parent.resolve()
        file_path = repo_dir
    if app is None:
        context = TextualAppContext(file_path=str(file_path))
        app = Browsr(config_object=context)
    screenshot = take_svg_screenshot(
        app=app,
        terminal_size=(160, 48),
        press=press or [],
        title=None,
    )
    return screenshot
