"""
The Primary Content Container
"""

from __future__ import annotations

import inspect
import pathlib
import shutil
from typing import Any

import pyperclip
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Mount
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import DirectoryTree
from textual_universal_directorytree import (
    UPath,
    is_remote_path,
)

from browsr.base import (
    TextualAppContext,
)
from browsr.config import favorite_themes
from browsr.utils import (
    get_file_info,
    handle_duplicate_filenames,
)
from browsr.widgets.base import BaseOverlay, BasePopUp
from browsr.widgets.confirmation import ConfirmationPopUp, ConfirmationWindow
from browsr.widgets.double_click_directory_tree import DoubleClickDirectoryTree
from browsr.widgets.files import CurrentFileInfoBar
from browsr.widgets.shortcuts import ShortcutsPopUp, ShortcutsWindow
from browsr.widgets.universal_directory_tree import BrowsrDirectoryTree
from browsr.widgets.windows import DataTableWindow, StaticWindow, WindowSwitcher


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
    selected_file_path: UPath | None | var[None] = var(None)

    def __init__(
        self,
        config_object: TextualAppContext,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Browsr Renderer
        """
        super().__init__(*args, **kwargs)
        self.config_object = config_object
        # Path Handling
        file_path = self.config_object.path
        if not file_path.exists():
            msg = f"Unknown File Path: {file_path}"
            raise FileNotFoundError(msg)
        elif file_path.is_file():
            self.selected_file_path = file_path  # type: ignore[assignment]
            file_path = file_path.parent
        elif file_path.is_dir() and file_path.joinpath("README.md").exists():
            self.selected_file_path = file_path.joinpath("README.md")  # type: ignore[assignment]
            self.force_show_tree = True
        self.initial_file_path = file_path
        self.directory_tree = BrowsrDirectoryTree(file_path, id="tree-view")
        self.window_switcher = WindowSwitcher(config_object=self.config_object)
        self.confirmation = ConfirmationPopUp()
        self.confirmation_window = ConfirmationWindow(
            self.confirmation, id="confirmation-container"
        )
        self.confirmation_window.display = False
        self.shortcuts = ShortcutsPopUp()
        self.shortcuts_window = ShortcutsWindow(
            self.shortcuts, id="shortcuts-container"
        )
        self.shortcuts_window.display = False
        self._content_display_state: dict[Widget, bool] = {}
        self._overlay_history: list[BaseOverlay] = []
        self._overlay_popup_map: dict[BaseOverlay, BasePopUp] = {
            self.confirmation_window: self.confirmation,
            self.shortcuts_window: self.shortcuts,
        }
        # Copy Pasting
        self._copy_function = pyperclip.determine_clipboard()[0]
        self._copy_supported = inspect.isfunction(self._copy_function)

    @property
    def datatable_window(self) -> DataTableWindow:
        """
        Get the datatable window
        """
        return self.window_switcher.datatable_window

    @property
    def static_window(self) -> StaticWindow:
        """
        Get the static window
        """
        return self.window_switcher.static_window

    def compose(self) -> ComposeResult:
        """
        Compose the content of the container
        """
        yield self.directory_tree
        yield self.window_switcher
        yield self.confirmation_window
        yield self.shortcuts_window

    @on(Mount)
    def bind_keys(self) -> None:
        """
        Bind Keys
        """
        if self._copy_supported:
            self.app.bind(
                keys="c", action="copy_file_path", description="Copy Path", show=False
            )
            self.app.bind(
                keys="C",
                action="copy_text",
                description="Copy Text",
                show=False,
                key_display="shift+c",
            )

        if is_remote_path(self.initial_file_path):  # type: ignore[arg-type]
            self.app.bind(
                keys="x", action="download_file", description="Download", show=True
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
        if self.selected_file_path and self._copy_supported:
            self._copy_function(str(self.selected_file_path))
            self.notify(
                message=f"{self.selected_file_path}",
                title="Copied to Clipboard",
                severity="information",
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

    @on(ConfirmationPopUp.DisplayToggle)
    def handle_confirmation_window_display_toggle(
        self, _: ConfirmationPopUp.DisplayToggle
    ) -> None:
        """
        Handle the confirmation window display toggle.
        """
        self._close_overlay(self.confirmation_window)

    @on(ShortcutsPopUp.DisplayToggle)
    def handle_shortcuts_window_display_toggle(
        self, _: ShortcutsPopUp.DisplayToggle
    ) -> None:
        """
        Handle the shortcuts window display toggle.
        """
        self._close_overlay(self.shortcuts_window)

    def _get_content_window_display_state(self) -> dict[Widget, bool]:
        """
        Capture the current content window visibility state.
        """
        return {
            self.window_switcher.datatable_window: (
                self.window_switcher.datatable_window.display
            ),
            self.window_switcher.text_window: self.window_switcher.text_window.display,
            self.window_switcher.vim_scroll: self.window_switcher.vim_scroll.display,
        }

    def _hide_content_windows(self) -> None:
        """
        Hide the content windows while an overlay is active.
        """
        self.window_switcher.datatable_window.display = False
        self.window_switcher.text_window.display = False
        self.window_switcher.vim_scroll.display = False

    def _restore_content_windows(self) -> None:
        """
        Restore the content windows after all overlays are closed.
        """
        for widget, state in self._content_display_state.items():
            widget.display = state
        active_widget = self.window_switcher.get_active_widget()
        if active_widget is not None:
            active_widget.focus()

    def _get_active_overlay(self) -> BaseOverlay | None:
        """
        Get the currently active overlay.
        """
        if not self._overlay_history:
            return None
        return self._overlay_history[-1]

    def _focus_overlay(self, overlay: BaseOverlay) -> None:
        """
        Focus the popup inside the active overlay.
        """
        self._overlay_popup_map[overlay].focus()

    def _show_overlay(self, overlay: BaseOverlay) -> None:
        """
        Display an overlay while preserving the last content window state.
        """
        active_overlay = self._get_active_overlay()
        if active_overlay is None:
            self._content_display_state = self._get_content_window_display_state()
            self._hide_content_windows()
        elif active_overlay is not overlay:
            active_overlay.display = False

        if overlay in self._overlay_history:
            self._overlay_history.remove(overlay)
        self._overlay_history.append(overlay)
        overlay.display = True
        self._focus_overlay(overlay)

    def _close_overlay(self, overlay: BaseOverlay) -> None:
        """
        Close an overlay and restore the previous overlay or content window.
        """
        if overlay in self._overlay_history:
            was_active_overlay = self._overlay_history[-1] is overlay
            self._overlay_history.remove(overlay)
            overlay.display = False
            if was_active_overlay and self._overlay_history:
                previous_overlay = self._overlay_history[-1]
                previous_overlay.display = True
                self._focus_overlay(previous_overlay)
            elif was_active_overlay:
                self._restore_content_windows()
        else:
            overlay.display = False

    @on(DirectoryTree.FileSelected)
    def handle_file_selected(self, message: DirectoryTree.FileSelected) -> None:
        """
        Called when the user click a file in the directory tree.
        """
        self.selected_file_path = message.path  # type: ignore[assignment]
        file_info = get_file_info(file_path=self.selected_file_path)  # type: ignore[arg-type]
        self.window_switcher.render_file(file_path=self.selected_file_path)  # type: ignore[arg-type]
        self.post_message(CurrentFileInfoBar.FileInfoUpdate(new_file=file_info))

    @on(DoubleClickDirectoryTree.DirectoryDoubleClicked)
    def handle_directory_double_click(
        self, message: DoubleClickDirectoryTree.DirectoryDoubleClicked
    ) -> None:
        """
        Called when the user double clicks a directory in the directory tree.
        """
        self.directory_tree.path = message.path
        self.notify(
            title="Directory Changed",
            message=str(message.path),
            severity="information",
            timeout=1,
        )

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
            if self._get_active_overlay() is self.confirmation_window:
                self._close_overlay(self.confirmation_window)
                return
            handled_download_path = self._get_download_file_name()
            self.confirmation.prompt_download(
                file_path=str(self.selected_file_path),
                download_path=str(handled_download_path),
            )
            self._show_overlay(self.confirmation_window)

    def toggle_shortcuts(self) -> None:
        """
        Toggle the shortcuts window.
        """
        if self._get_active_overlay() is self.shortcuts_window:
            self._close_overlay(self.shortcuts_window)
        else:
            self.shortcuts.update_shortcuts()
            self._show_overlay(self.shortcuts_window)

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
                timeout=2,
            )

    def _get_download_file_name(self) -> UPath | pathlib.Path:
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
