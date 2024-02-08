"""
Browsr TUI App

This module contains the code browser app for the browsr package.
This app was inspired by the CodeBrowser example from textual
"""

from __future__ import annotations

import os
from os import getenv
from typing import Any, ClassVar

from textual import on
from textual.binding import Binding, BindingType
from textual.events import Mount

from browsr.__about__ import __application__
from browsr.base import (
    SortedBindingsApp,
    TextualAppContext,
)
from browsr.screens import CodeBrowserScreen


class Browsr(SortedBindingsApp):
    """
    Textual code browser app.
    """

    TITLE = __application__
    CSS_PATH = "browsr.css"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="d", action="toggle_dark", description="Dark Mode"),
    ]
    BINDING_WEIGHTS: ClassVar[dict[str, int]] = {
        "ctrl+c": 1,
        "q": 2,
        "f": 3,
        "t": 4,
        "n": 5,
        "d": 6,
        "r": 995,
        ".": 996,
        "c": 997,
        "x": 998,
    }

    def __init__(
        self,
        config_object: TextualAppContext | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Like the textual.app.App class, but with an extra config_object property

        Parameters
        ----------
        config_object: Optional[TextualAppContext]
            A configuration object. This is an optional python object,
            like a dictionary to pass into an application
        """
        super().__init__(*args, **kwargs)
        self.config_object = config_object or TextualAppContext()
        self.code_browser_screen = CodeBrowserScreen(config_object=self.config_object)
        self.install_screen(self.code_browser_screen, name="code-browser")

    @on(Mount)
    async def mount_screen(self) -> None:
        """
        Mount the screen
        """
        await self.push_screen(screen=self.code_browser_screen)

    def action_copy_file_path(self) -> None:
        """
        Copy the file path to the clipboard
        """
        self.code_browser_screen.code_browser.copy_file_path()

    def action_download_file(self) -> None:
        """
        Copy the file path to the clipboard
        """
        self.code_browser_screen.code_browser.download_file_workflow()


app = Browsr(
    config_object=TextualAppContext(
        file_path=getenv("BROWSR_PATH", os.getcwd()), debug=True
    )
)

if __name__ == "__main__":
    app.run()
