"""
The App Screen
"""

from __future__ import annotations

import pathlib
from typing import ClassVar, Iterable

from rich import traceback
from textual import on
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.events import Mount
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from browsr.base import TextualAppContext
from browsr.utils import get_file_info
from browsr.widgets.code_browser import CodeBrowser
from browsr.widgets.files import CurrentFileInfoBar


class CodeBrowserScreen(Screen):
    """
    Code Browser Screen
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="f", action="toggle_files", description="Files"),
        Binding(key="t", action="theme", description="Theme"),
        Binding(key="n", action="linenos", description="Line Numbers"),
        Binding(key="r", action="reload", description="Reload"),
        Binding(key=".", action="parent_dir", description="Parent Directory"),
    ]

    def __init__(
        self,
        config_object: TextualAppContext | None = None,
    ) -> None:
        """
        Like the textual.app.App class, but with an extra config_object property

        Parameters
        ----------
        config_object: Optional[TextualAppContext]
            A configuration object. This is an optional python object,
            like a dictionary to pass into an application
        """
        super().__init__()
        self.config_object = config_object or TextualAppContext()
        traceback.install(show_locals=True)
        self.header = Header()
        self.code_browser = CodeBrowser(config_object=self.config_object)
        self.file_information = CurrentFileInfoBar()
        self.info_bar = Horizontal(
            self.file_information,
            id="file-info-bar",
        )
        if self.code_browser.selected_file_path is not None:
            self.file_information.file_info = get_file_info(
                file_path=self.code_browser.selected_file_path
            )
        self.footer = Footer()

    def compose(self) -> Iterable[Widget]:
        """
        Compose our UI.
        """
        yield self.header
        yield self.code_browser
        yield self.info_bar
        yield self.footer

    @on(Mount)
    def start_up_app(self) -> None:
        """
        On Application Mount - See If a File Should be Displayed
        """
        if self.code_browser.selected_file_path is not None:
            self.code_browser.show_tree = self.code_browser.force_show_tree
            self.code_browser.window_switcher.render_file(
                file_path=self.code_browser.selected_file_path
            )
            if (
                self.code_browser.show_tree is False
                and self.code_browser.window_switcher.text_area.display is True
            ):
                self.code_browser.window_switcher.focus()
            elif (
                self.code_browser.show_tree is False
                and self.code_browser.window_switcher.datatable_window.display is True
            ):
                self.code_browser.window_switcher.datatable_window.focus()
        else:
            self.code_browser.show_tree = True
            self.code_browser.window_switcher.render_file(file_path=pathlib.Path.cwd())

    @on(CurrentFileInfoBar.FileInfoUpdate)
    def update_file_info(self, message: CurrentFileInfoBar.FileInfoUpdate) -> None:
        """
        Update the file_info property
        """
        self.file_information.file_info = message.new_file

    def action_toggle_files(self) -> None:
        """
        Called in response to key binding.
        """
        self.code_browser.show_tree = not self.code_browser.show_tree

    def action_parent_dir(self) -> None:
        """
        Go to the parent directory
        """
        new_path = self.config_object.path.parent.resolve()
        if new_path != self.config_object.path:
            self.config_object.file_path = str(new_path)
            self.code_browser.directory_tree.path = new_path
            self.notify(
                title="Directory Changed",
                message=str(new_path),
                severity="information",
                timeout=1,
            )

    def action_theme(self) -> None:
        """
        An action to toggle rich theme.
        """
        themes = list(self.code_browser.window_switcher.text_area.available_themes)
        current_index = themes.index(self.code_browser.window_switcher.text_area.theme)
        try:
            self.code_browser.window_switcher.text_area.theme = themes[
                current_index + 1
            ]
        except IndexError:
            self.code_browser.window_switcher.text_area.theme = themes[0]

    def action_linenos(self) -> None:
        """
        An action to toggle line numbers.
        """
        if self.code_browser.selected_file_path is None:
            return
        self.code_browser.window_switcher.text_area.show_line_numbers = (
            not self.code_browser.window_switcher.text_area.show_line_numbers
        )

    def action_reload(self) -> None:
        """
        Refresh the directory.
        """
        self.code_browser.directory_tree.reload()
        self.notify(
            title="Directory Reloaded",
            message=str(self.code_browser.directory_tree.path),
            severity="information",
            timeout=1,
        )

    def action_copy_selected_text(self) -> None:
        """
        Copy the selected text
        """
        if self.code_browser._copy_supported:
            self.code_browser._copy_function(
                self.code_browser.window_switcher.text_area.selected_text
            )
