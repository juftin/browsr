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
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.events import Mount

from browsr.__about__ import __application__
from browsr.base import (
    TextualAppContext,
)
from browsr.screens import CodeBrowserScreen
from browsr.widgets.shortcuts import ShortcutsPopUp, ShortcutsWindow


class Browsr(App[str]):
    """
    Textual code browser app.
    """

    TITLE = __application__
    CSS_PATH = "browsr.css"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="d", action="toggle_dark", description="Dark Mode"),
        Binding(key="?", action="toggle_shortcuts", description="Shortcuts"),
    ]

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

    def compose(self) -> ComposeResult:
        """
        Compose the app
        """
        self.shortcuts_window = ShortcutsWindow(id="shortcuts-container")
        yield self.shortcuts_window

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

    def action_copy_text(self) -> None:
        """
        An action to copy text.
        """
        self.code_browser_screen.code_browser.window_switcher.text_window.copy_selected_text()

    def action_toggle_shortcuts(self) -> None:
        """
        Toggle the shortcuts window
        """
        self.shortcuts_window.display = not self.shortcuts_window.display
        if self.shortcuts_window.display:
            self.shortcuts_window.query_one(ShortcutsPopUp).update_shortcuts()
            self.shortcuts_window.focus()


app = Browsr(
    config_object=TextualAppContext(
        file_path=getenv("BROWSR_PATH", os.getcwd()), debug=True
    )
)

if __name__ == "__main__":
    app.run()
