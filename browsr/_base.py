"""
Extension Classes
"""

from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, ClassVar, Dict, List, Optional, Union

import numpy as np
import upath
from pandas import DataFrame
from rich import traceback
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Button, DataTable, Static

from browsr._config import favorite_themes
from browsr._utils import FileInfo, handle_github_url


@dataclass
class TextualAppContext:
    """
    App Context Object
    """

    file_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    debug: bool = False
    max_file_size: int = 20

    @property
    def path(self) -> pathlib.Path:
        """
        Resolve `file_path` to a upath.UPath object
        """
        if "github" in str(self.file_path).lower():
            file_path = str(self.file_path)
            file_path = file_path.lstrip("https://")
            file_path = file_path.lstrip("http://")
            file_path = file_path.lstrip("www.")
            if file_path.endswith(".git"):
                file_path = file_path[:-4]
            file_path = handle_github_url(url=str(file_path))
            self.file_path = file_path
        if str(self.file_path).endswith("/"):
            self.file_path = str(self.file_path)[:-1]
        return (
            upath.UPath(self.file_path).resolve()
            if self.file_path
            else pathlib.Path.cwd().resolve()
        )


class BrowsrTextualApp(App[str]):
    """
    textual.app.App Extension
    """

    show_tree = var(True)
    theme_index = var(0)
    linenos = var(False)
    rich_themes = favorite_themes
    selected_file_path: Union[upath.UPath, pathlib.Path, None, var[None]] = var(None)
    force_show_tree = var(False)
    hidden_table_view = var(False)

    def __init__(
        self,
        config_object: Optional[TextualAppContext] = None,
    ):
        """
        Like the textual.app.App class, but with an extra config_object property

        Parameters
        ----------
        config_object: Optional[TextualAppContext]
            A configuration object. This is an optional python object,
            like a dictionary to pass into an application
        """
        super().__init__()
        self.config_object = config_object
        traceback.install(show_locals=True)

    @staticmethod
    def df_to_table(
        pandas_dataframe: DataFrame,
        table: DataTable[str],
        show_index: bool = True,
        index_name: Optional[str] = None,
    ) -> DataTable[str]:
        """
        Convert a pandas.DataFrame obj into a rich.Table obj.

        Parameters
        ----------
        pandas_dataframe: DataFrame
            A Pandas DataFrame to be converted to a rich Table.
        table: DataTable[str]
            A DataTable that should be populated by the DataFrame values.
        show_index: bool
            Add a column with a row count to the table. Defaults to True.
        index_name: Optional[str]
            The column name to give to the index column. Defaults to None, showing no value.

        Returns
        -------
        DataTable[str]
            The DataTable instance passed, populated with the DataFrame values.
        """
        table.clear(columns=True)
        if show_index:
            index_name = str(index_name) if index_name else ""
            table.add_column(index_name)
        for column in pandas_dataframe.columns:
            table.add_column(str(column))
        pandas_dataframe.replace([np.NaN], [""], inplace=True)
        for index, value_list in enumerate(pandas_dataframe.values.tolist()):
            row = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            table.add_row(*row)
        return table


class FileSizeError(Exception):
    """
    File Too Large Error
    """


class CurrentFileInfoBar(Widget):
    """
    A Widget that displays information about the currently selected file

    Thanks, Kupo. https://github.com/darrenburns/kupo
    """

    file_info: Union[FileInfo, var[None]] = reactive(None)  # type: ignore[assignment]

    def watch_file_info(self, new_file: Union[FileInfo, None]) -> None:
        """
        Watch the file_info property for changes
        """
        if new_file is None:
            self.display = False
        else:
            self.display = True

    @classmethod
    def _convert_size(cls, size_bytes: int) -> str:
        """
        Convert Bytes to Human Readable String
        """
        if size_bytes == 0:
            return " 0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        index = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, index)
        number = round(size_bytes / p, 2)
        unit = size_name[index]
        return f"{number:.0f}{unit}"

    def render(self) -> RenderableType:
        """
        Render the Current File Info Bar
        """
        if self.file_info is None or not self.file_info.is_file:
            return Text("")
        status_string = "🗄️️️  " + self._convert_size(self.file_info.size)
        if self.file_info.last_modified is not None:
            modify_time = self.file_info.last_modified.strftime("%b %d, %Y %I:%M %p")
            status_string += "  📅  " + modify_time
        status_string += (
            "  💾  "
            + self.file_info.file.name
            + "  📂  "
            + self.file_info.file.parent.name
        )
        if self.file_info.owner not in ["", None]:
            status_string += "  👤  " + self.file_info.owner
        if self.file_info.group.strip() not in ["", None]:
            status_string += "  🏠  " + self.file_info.group
        return Text(status_string, style="dim")


class ConfirmationPopUp(Container):
    """
    A Pop Up that asks for confirmation
    """

    __confirmation_message__: str = dedent(
        """
        ## File Download

        Are you sure you want to download that file?
        """
    )

    def compose(self) -> ComposeResult:
        """
        Compose the Confirmation Pop Up
        """
        self.download_message = Static(Markdown(""))
        yield self.download_message
        yield Button("Yes", variant="success")
        yield Button("No", variant="error")

    @on(Button.Pressed)
    def handle_download_selection(self, message: Button.Pressed) -> None:
        """
        Handle Button Presses
        """
        self.app.confirmation_window.display = False  # type: ignore[attr-defined]
        if message.button.variant == "success":
            self.app.download_selected_file()  # type: ignore[attr-defined]
        self.app.table_view.display = self.app.hidden_table_view  # type: ignore[attr-defined]


vim_scroll_bindings = [
    Binding(key="k", action="scroll_up", description="Scroll Up", show=False),
    Binding(key="j", action="scroll_down", description="Scroll Down", show=False),
    Binding(key="h", action="scroll_left", description="Scroll Left", show=False),
    Binding(key="l", action="scroll_right", description="Scroll Right", show=False),
]

vim_cursor_bindings = [
    Binding(key="k", action="cursor_up", description="Cursor Up", show=False),
    Binding(key="j", action="cursor_down", description="Cursor Down", show=False),
    Binding(key="h", action="cursor_left", description="Cursor Left", show=False),
    Binding(key="l", action="cursor_right", description="Cursor Right", show=False),
]


class VimScroll(VerticalScroll):
    """
    A VerticalScroll with Vim Keybindings
    """

    BINDINGS: ClassVar[List[BindingType]] = [
        *VerticalScroll.BINDINGS,
        *vim_scroll_bindings,
    ]


class VimDataTable(DataTable[str]):
    """
    A DataTable with Vim Keybindings
    """

    BINDINGS: ClassVar[List[BindingType]] = [
        *DataTable.BINDINGS,
        *vim_cursor_bindings,
    ]
