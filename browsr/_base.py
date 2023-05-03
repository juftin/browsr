"""
Extension Classes
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import rich_click as click
import upath
from pandas import DataFrame
from textual.app import App
from textual.widgets import DataTable, DirectoryTree
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode
from upath import UPath

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

    @property
    def path(self) -> pathlib.Path:
        """
        Resolve `file_path` to a upath.UPath object
        """

        return (
            upath.UPath(self.file_path).resolve()
            if self.file_path
            else pathlib.Path.cwd().resolve()
        )


class BrowsrTextualApp(App[str]):
    """
    textual.app.App Extension
    """

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


@dataclass
class BrowsrClickContext:
    """
    Context Object to Pass Around CLI
    """

    debug: bool


class UniversalDirectoryTree(DirectoryTree):
    """
    A Universal DirectoryTree supporting different filesystems
    """

    def load_directory(self, node: TreeNode[DirEntry]) -> None:
        """
        Load Directory Using Universal Pathlib
        """
        assert node.data is not None
        dir_path = UPath(node.data.path)
        node.data.loaded = True
        directory = sorted(
            dir_path.iterdir(),
            key=lambda path: (not path.is_dir(), path.name.lower()),
        )
        for path in directory:
            node.add(
                path.name,
                data=DirEntry(str(path), path.is_dir()),
                allow_expand=path.is_dir(),
            )
        node.expand()


class FileSizeError(Exception):
    """
    File Too Large Error
    """
