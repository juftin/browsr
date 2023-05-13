"""
Extension Classes
"""

from __future__ import annotations

import math
import pathlib
import stat
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import rich_click as click
import upath
from pandas import DataFrame
from rich import traceback
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Button, DataTable, DirectoryTree, Static
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode
from upath import UPath

from browsr._config import favorite_themes
from browsr._utils import FileInfo

debug_option = click.option(
    "--debug/--no-debug", default=False, help="Enable extra debugging output"
)


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


class UniversalDirectoryTree(DirectoryTree):
    """
    A Universal DirectoryTree supporting different filesystems
    """

    def _load_directory(self, node: TreeNode[DirEntry]) -> None:
        """
        Load Directory Using Universal Pathlib
        """
        assert node.data is not None
        dir_path = UPath(node.data.path)
        node.data.loaded = True
        top_level_buckets = self._handle_top_level_bucket(dir_path=dir_path)
        if top_level_buckets is None:
            directory = sorted(
                dir_path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
        for path in top_level_buckets or directory:
            if top_level_buckets is None:
                path_name = path.name
            else:
                path_name = str(path).replace("s3://", "").rstrip("/")
            node.add(
                path_name,
                data=DirEntry(path),
                allow_expand=path.is_dir(),
            )
        node.expand()

    def reload(self) -> None:
        """
        Reload the `DirectoryTree` contents.
        """
        self.reset(str(self.path), DirEntry(UPath(self.path)))
        self._load_directory(self.root)

    def validate_path(self, path: Union[str, UPath]) -> UPath:  # type: ignore[override]
        """
        Ensure that the path is of the `UPath` type.
        """
        return UPath(path)

    def _handle_top_level_bucket(self, dir_path: UPath) -> Optional[Iterable[UPath]]:
        """
        Handle scenarios when someone wants to browse all of s3

        This is because S3FS handles the root directory differently than other filesystems
        """
        if str(dir_path) == "s3:/":
            sub_buckets = sorted(
                UPath(f"s3://{bucket.name}") for bucket in dir_path.iterdir()
            )
            return sub_buckets
        return None


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
        Watch the file property for changes
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
            return " 0[dim]B"
        size_name = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
        index = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, index)
        number = round(size_bytes / p, 2)
        unit = size_name[index]
        return f"{number:.0f}[dim]{unit}[/]"

    @classmethod
    def _render_mode_string(cls, file_info: FileInfo) -> List[Any]:
        """
        Render the Mode String for the Current File Info Bar
        """
        if file_info.is_local is False:
            return [("----------", "dim"), (" ╲ ", "dim cyan")]
        perm_string = stat.filemode(file_info.stat.st_mode)  # type: ignore[union-attr]
        perm_string = Text.assemble(  # type: ignore[assignment]
            (perm_string[0], "b dim"),
            (perm_string[1], "yellow b" if perm_string[1] == "r" else "dim"),
            (perm_string[2], "red b" if perm_string[2] == "w" else "dim"),
            (perm_string[3], "green b" if perm_string[3] == "x" else "dim"),
            (perm_string[4], "yellow b" if perm_string[4] == "r" else "dim"),
            (perm_string[5], "red b" if perm_string[5] == "w" else "dim"),
            (perm_string[6], "green b" if perm_string[6] == "x" else "dim"),
            (perm_string[7], "b yellow" if perm_string[7] == "r" else "dim"),
            (perm_string[8], "b red" if perm_string[8] == "w" else "dim"),
            (perm_string[9], "b green" if perm_string[9] == "x" else "dim"),
        )
        assembled = [
            perm_string,
            (" ╲ ", "dim cyan"),
        ]
        return assembled

    def render(self) -> RenderableType:
        """
        Render the Current File Info Bar
        """
        if self.file_info is None:
            return Text("")
        modify_time = self.file_info.last_modified.strftime("%-d %b %y %H:%M")
        assembled = self._render_mode_string(file_info=self.file_info)
        if self.file_info.is_file:
            assembled += [
                Text.from_markup(self._convert_size(self.file_info.size)),
                (" ╲ ", "dim cyan"),
            ]
        assembled += [
            modify_time,
            (" ╲ ", "dim cyan"),
            self.file_info.owner,
            (" ╲ ", "dim cyan"),
            self.file_info.group,
        ]

        return Text.assemble(*assembled)


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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle Button Presses
        """
        self.app.confirmation_window.display = False  # type: ignore[attr-defined]
        if event.button.variant == "success":
            self.app.download_selected_file()  # type: ignore[attr-defined]
        self.app.table_view.display = self.app.hidden_table_view  # type: ignore[attr-defined]
