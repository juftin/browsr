"""
The App Screen
"""

import pathlib
from typing import Iterable

from rich import traceback
from textual import on
from textual.containers import Horizontal
from textual.events import Mount
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from browsr.__about__ import __application__
from browsr.base import TextualAppContext
from browsr.utils import get_file_info
from browsr.widgets.code_browser import CodeBrowser
from browsr.widgets.files import CurrentFileInfoBar


class CodeBrowserScreen(Screen):
    """
    Code Browser Screen
    """

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
            self.code_browser.render_code_page(
                file_path=self.code_browser.selected_file_path
            )
            if (
                self.code_browser.show_tree is False
                and self.code_browser.code_view.display is True
            ):
                self.code_browser.code_view.focus()
            elif (
                self.code_browser.show_tree is False
                and self.code_browser.table_view.display is True
            ):
                self.code_browser.table_view.focus()
        else:
            self.code_browser.show_tree = True
            self.code_browser.render_code_page(
                file_path=pathlib.Path.cwd(), content=__application__.upper()
            )

    @on(CurrentFileInfoBar.FileInfoUpdate)
    def update_file_info(self, message: CurrentFileInfoBar.FileInfoUpdate) -> None:
        """
        Update the file_info property
        """
        self.file_information.file_info = message.new_file
