"""
The Primary Content Container
"""

from __future__ import annotations

import inspect
import pathlib
import shutil
from textwrap import dedent
from typing import Any

import pyperclip
import textual
import upath
from rich.markdown import Markdown
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Mount
from textual.reactive import var
from textual.widgets import DirectoryTree
from textual_universal_directorytree import is_remote_path

from browsr.base import (
    TextualAppContext,
)
from browsr.config import favorite_themes
from browsr.utils import (
    get_file_info,
    handle_duplicate_filenames,
)
from browsr.widgets.confirmation import ConfirmationPopUp, ConfirmationWindow
from browsr.widgets.double_click_directory_tree import DoubleClickDirectoryTree
from browsr.widgets.files import CurrentFileInfoBar
from browsr.widgets.universal_directory_tree import BrowsrDirectoryTree
from browsr.widgets.windows import WindowSwitcher


class CodeBrowser(Container):
    """
    The Code Browser

    This container contains the primary content of the application:

    - Universal Directory Tree
    - Space to view the selected file:
        - Code
        - Table
        - Image
        - Exceptions
    """

    theme_index = var(0)
    rich_themes = favorite_themes
    show_tree = var(True)
    force_show_tree = var(False)
    hidden_table_view = var(False)
    selected_file_path: upath.UPath | pathlib.Path | None | var[None] = var(None)

    def __init__(
        self,
        *args: Any,
        config_object: TextualAppContext,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Browsr Renderer
        """
        super().__init__(*args, **kwargs)
        self.config_object = config_object
        # Path Handling
        file_path = self.config_object.path
        if file_path.is_file():
            self.selected_file_path = file_path
            file_path = file_path.parent
        elif file_path.is_dir() and file_path.joinpath("README.md").exists():
            self.selected_file_path = file_path.joinpath("README.md")
            self.force_show_tree = True
        self.initial_file_path = file_path
        # Widget Initialization
        self.directory_tree = BrowsrDirectoryTree(str(file_path), id="tree-view")
        self.window_switcher = WindowSwitcher()
        self.confirmation = ConfirmationPopUp()
        self.confirmation_window = ConfirmationWindow(
            self.confirmation, id="confirmation-container"
        )
        self.confirmation_window.display = False
        # Copy Pasting
        self._copy_function = pyperclip.determine_clipboard()[0]
        self._copy_supported = inspect.isfunction(self._copy_function)

    def compose(self) -> ComposeResult:
        """
        Compose the content of the container
        """
        yield self.directory_tree
        yield self.window_switcher
        yield self.confirmation_window

    @on(Mount)
    def bind_keys(self) -> None:
        """
        Bind Keys
        """
        if self._copy_supported:
            self.app.bind(
                keys="c", action="copy_file_path", description="Copy Path", show=True
            )
        if is_remote_path(self.initial_file_path):
            self.app.bind(
                keys="x", action="download_file", description="Download File", show=True
            )

    def watch_show_tree(self, show_tree: bool) -> None:
        """
        Called when show_tree is modified.
        """
        self.set_class(show_tree, "-show-tree")

    def copy_file_path(self) -> None:
        """
        Copy the file path to the clipboard.
        """
        if self.selected_file_path:
            try:
                pyperclip.copy(str(self.selected_file_path))
                self.notify(
                    message=f"{self.selected_file_path}",
                    title="Copied to Clipboard",
                    severity="information",
                    timeout=1,
                )
            except pyperclip.PyperclipException:
                self.notify(
                    message="copy/pase not supported on this platform",
                    title="Error Copying to Clipboard",
                    severity="warning",
                    timeout=1,
                )

    @on(ConfirmationPopUp.ConfirmationWindowDownload)
    def handle_download_confirmation(
        self, _: ConfirmationPopUp.ConfirmationWindowDownload
    ) -> None:
        """
        Handle the download confirmation.
        """
        self.download_selected_file()

    @on(ConfirmationPopUp.TableViewDisplayToggle)
    def handle_table_view_display_toggle(
        self, _: ConfirmationPopUp.TableViewDisplayToggle
    ) -> None:
        """
        Handle the table view display toggle.
        """
        self.table_view.display = self.hidden_table_view

    @on(DirectoryTree.FileSelected)
    def handle_file_selected(self, message: DirectoryTree.FileSelected) -> None:
        """
        Called when the user click a file in the directory tree.
        """
        self.selected_file_path = upath.UPath(message.path)
        file_info = get_file_info(file_path=self.selected_file_path)
        self.window_switcher.render_file(file_path=self.selected_file_path)
        self.post_message(CurrentFileInfoBar.FileInfoUpdate(new_file=file_info))

    @on(DoubleClickDirectoryTree.DirectoryDoubleClicked)
    def handle_directory_double_click(
        self, message: DoubleClickDirectoryTree.DirectoryDoubleClicked
    ) -> None:
        """
        Called when the user double clicks a directory in the directory tree.
        """
        self.directory_tree.path = message.path
        self.config_object.file_path = str(message.path)

    @on(DoubleClickDirectoryTree.FileDoubleClicked)
    def handle_file_double_click(
        self, message: DoubleClickDirectoryTree.FileDoubleClicked
    ) -> None:
        """
        Called when the user double clicks a file in the directory tree.
        """
        if self._copy_supported:
            self._copy_function(str(message.path))
            self.notify(
                message=f"{message.path}",
                title="Copied to Clipboard",
                severity="information",
                timeout=1,
            )

    def download_file_workflow(self) -> None:
        """
        Download the selected file.
        """
        if self.selected_file_path is None:
            return
        elif self.selected_file_path.is_dir():
            return
        elif is_remote_path(self.selected_file_path):
            handled_download_path = self._get_download_file_name()
            prompt_message: str = dedent(
                f"""
                ## File Download

                **Are you sure you want to download that file?**

                **File:** `{self.selected_file_path}`

                **Path:** `{handled_download_path}`
                """
            )
            self.confirmation.download_message.update(Markdown(prompt_message))
            self.confirmation.refresh()
            self.hidden_table_view = self.table_view.display
            self.table_view.display = False
            self.confirmation_window.display = True

    @work(thread=True)
    def download_selected_file(self) -> None:
        """
        Download the selected file.
        """
        if self.selected_file_path is None:
            return
        elif self.selected_file_path.is_dir():
            return
        elif is_remote_path(self.selected_file_path):
            handled_download_path = self._get_download_file_name()
            with self.selected_file_path.open("rb") as file_handle:
                with handled_download_path.open("wb") as download_handle:
                    shutil.copyfileobj(file_handle, download_handle)
            self.notify(
                message=str(handled_download_path),
                title="Download Complete",
                severity="information",
                timeout=1,
            )

    def _get_download_file_name(self) -> pathlib.Path:
        """
        Get the download file name.
        """
        download_dir = pathlib.Path.home() / "Downloads"
        if not download_dir.exists():
            msg = f"Download directory {download_dir} not found"
            raise FileNotFoundError(msg)
        download_path = download_dir / self.selected_file_path.name  # type: ignore[union-attr]
        handled_download_path = handle_duplicate_filenames(file_path=download_path)
        return handled_download_path

    @on(textual.events.Key)
    async def handle_key_press(self, event: textual.events.Key) -> None:
        """
        Handle Key Presses
        """
        textual.log(event)
