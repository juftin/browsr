"""
The App Screen
"""

from __future__ import annotations

from typing import ClassVar, Iterable, cast

from rich import traceback
from textual import on
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.events import Mount
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header
from textual_universal_directorytree import UPath

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
        else:
            self.file_information.file_info = get_file_info(self.config_object.path)
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
                and self.code_browser.static_window.display is True
            ):
                self.code_browser.window_switcher.focus()
            elif (
                self.code_browser.show_tree is False
                and self.code_browser.datatable_window.display is True
            ):
                self.code_browser.datatable_window.focus()
        else:
            self.code_browser.show_tree = True

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
        directory_tree_open = self.code_browser.has_class("-show-tree")
        if not directory_tree_open:
            return
        if (
            self.code_browser.directory_tree.path
            != self.code_browser.directory_tree.path.parent
        ):
            self.code_browser.directory_tree.path = (
                self.code_browser.directory_tree.path.parent
            )
            self.notify(
                title="Directory Changed",
                message=str(self.code_browser.directory_tree.path),
                severity="information",
                timeout=1,
            )

    def action_theme(self) -> None:
        """
        An action to toggle rich theme.
        """
        self.code_browser.window_switcher.next_theme()

    def action_linenos(self) -> None:
        """
        An action to toggle line numbers.
        """
        if self.code_browser.selected_file_path is None:
            return
        self.code_browser.static_window.linenos = (
            not self.code_browser.static_window.linenos
        )

    def action_reload(self) -> None:
        """
        Refresh the directory and file
        """
        reload_file = self.code_browser.selected_file_path is not None
        reload_directory = self.code_browser.has_class("-show-tree")
        message_lines = []
        if reload_directory:
            self.code_browser.directory_tree.reload()
            directory_name = self.code_browser.directory_tree.path.name or "/"
            message_lines.append(
                "[bold]Directory:[/bold] " f"[italic]{directory_name}[/italic]"
            )
        if reload_file:
            selected_file_path = cast(UPath, self.code_browser.selected_file_path)
            file_name = selected_file_path.name
            self.code_browser.window_switcher.render_file(
                file_path=selected_file_path,
                scroll_home=False,
            )
            message_lines.append("[bold]File:[/bold] " f"[italic]{file_name}[/italic]")
        if message_lines:
            self.notify(
                title="Reloaded",
                message="\n".join(message_lines),
                severity="information",
                timeout=1,
            )
