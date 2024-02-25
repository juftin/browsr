"""
Content Windows
"""

from __future__ import annotations

import json
import pathlib
from json import JSONDecodeError
from typing import Any, ClassVar

import numpy as np
import pandas as pd
from art import text2art
from rich.markdown import Markdown
from rich_pixels import Pixels
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.document._document import EditResult
from textual.events import Key
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import DataTable, Static, TextArea
from textual.widgets._text_area import Edit

from browsr.config import image_file_extensions
from browsr.exceptions import FileSizeError
from browsr.utils import (
    ArchiveFileError,
    FileInfo,
    open_image,
)


class BaseCodeWindow(Widget):
    """
    Base code view widget
    """

    archive_extensions: ClassVar[list[str]] = [".tar", ".gz", ".zip", ".tgz"]

    class WindowSwitch(Message):
        """
        Switch to the window
        """

        def __init__(self, window: type[BaseCodeWindow], scroll_home: bool = False):
            self.window: type[BaseCodeWindow] = window
            self.scroll_home: bool = scroll_home
            super().__init__()

    def file_to_string(self, file_path: pathlib.Path) -> str:
        """
        Load a file into a string
        """
        try:
            if file_path.suffix in self.archive_extensions:
                message = f"Cannot render archive file {file_path}."
                raise ArchiveFileError(message)
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            text = self.handle_exception(exception=e)
        return text

    def file_to_markdown(self, file_path: pathlib.Path) -> Markdown:
        """
        Load a file into a Markdown
        """
        return Markdown(
            self.file_to_string(file_path),
            # code_theme=self.rich_themes[self.theme_index],
            hyperlinks=True,
        )

    def file_to_image(self, file_path: pathlib.Path) -> Pixels:
        """
        Load a file into an image
        """
        screen_width = self.app.size.width / 4
        content = open_image(document=file_path, screen_width=screen_width)
        return content

    def file_to_json(self, file_path: pathlib.Path) -> str:
        """
        Load a file into a JSON object
        """
        code_str = self.file_to_string(file_path=file_path)
        try:
            code_obj = json.loads(code_str)
            return json.dumps(code_obj, indent=2)
        except JSONDecodeError:
            return code_str

    @classmethod
    def handle_file_size(cls, file_info: FileInfo, max_file_size: int = 5) -> None:
        """
        Handle a File Size
        """
        file_size_mb = file_info.size / 1000 / 1000
        too_large = file_size_mb >= max_file_size
        if too_large:
            raise FileSizeError("File too large")

    @classmethod
    def handle_exception(cls, exception: Exception) -> str:
        """
        Handle an exception

        This method is used to handle exceptions that occur when rendering a file.
        When an uncommon exception occurs, the method will raise the exception.

        Parameters
        ----------
        exception: Exception
            The exception that occurred.

        Raises
        ------
        Exception
            If the exception is not one of the expected exceptions.

        Returns
        -------
        str
            The error message to display.
        """
        font = "univers"
        if isinstance(exception, ArchiveFileError):
            error_message = (
                text2art("ARCHIVE", font=font) + "\n\n" + text2art("FILE", font=font)
            )
        elif isinstance(exception, FileSizeError):
            error_message = (
                text2art("FILE TOO", font=font) + "\n\n" + text2art("LARGE", font=font)
            )
        elif isinstance(exception, PermissionError):
            error_message = (
                text2art("PERMISSION", font=font)
                + "\n\n"
                + text2art("ERROR", font=font)
            )
        elif isinstance(exception, UnicodeError):
            error_message = (
                text2art("ENCODING", font=font) + "\n\n" + text2art("ERROR", font=font)
            )
        else:
            raise exception from exception
        return error_message


class StaticWindow(Static, BaseCodeWindow):
    """
    A static widget for displaying code.
    """


class TextAreaWindow(TextArea, BaseCodeWindow):
    """
    A widget for displaying code.
    """

    editable: bool = var(False)
    language_mapping: ClassVar[dict[str, str]] = {
        ".sh": "bash",
        ".bash": "bash",
        ".c": "c",
        ".cs": "c-sharp",
        ".lisp": "commonlisp",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".h": "cpp",  # Note: .h could be C or C++ header, context needed
        ".css": "css",
        ".Dockerfile": "dockerfile",
        ".dot": "dot",
        ".el": "elisp",
        ".ex": "elixir",
        ".exs": "elixir",
        ".elm": "elm",
        ".erl": "erlang",
        ".hrl": "erlang",
        ".f": "fixed-form-fortran",
        ".for": "fixed-form-fortran",
        ".f90": "fortran",
        ".f95": "fortran",
        ".go": "go",
        ".mod": "go-mod",
        ".hack": "hack",
        ".hs": "haskell",
        ".lhs": "haskell",
        ".hcl": "hcl",
        ".html": "html",
        ".htm": "html",
        ".java": "java",
        ".js": "javascript",
        ".mjs": "javascript",
        ".jsdoc": "jsdoc",
        ".json": "json",
        ".jl": "julia",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".lua": "lua",
        ".mak": "make",
        ".mk": "make",
        ".md": "markdown",
        ".markdown": "markdown",
        ".m": "objc",
        ".mm": "objc",  # Objective-C++
        ".ml": "ocaml",
        ".mli": "ocaml",
        ".pl": "perl",
        ".pm": "perl",
        ".php": "php",
        ".phtml": "php",
        ".php3": "php",
        ".php4": "php",
        ".php5": "php",
        ".php7": "php",
        ".phps": "php",
        ".py": "python",
        ".rpy": "python",
        ".ql": "ql",
        ".r": "r",
        ".regex": "regex",
        ".rst": "rst",
        ".rb": "ruby",
        ".rs": "rust",
        ".scala": "scala",
        ".sc": "scala",
        ".sql": "sql",
        ".sqlite3": "sqlite",
        ".toml": "toml",
        ".tsq": "tsq",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".yaml": "yaml",
        ".yml": "yaml",
    }

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(
            key="shift+c",
            action="copy_selected_text",
            description="Copy Text",
            show=True,
        )
    ]

    def edit(self, edit: Edit) -> EditResult | None:
        """
        Control whether the TextArea is editable
        """
        if self.editable:
            return super().edit(edit=edit)

    async def _on_key(self, event: Key) -> None:
        """
        Control whether the TextArea is editable
        """
        if self.editable:
            await super()._on_key(event=event)
        else:
            event.stop()
            event.prevent_default()
            await self.app.check_bindings(key=event.key)

    def render_file_size_error(self) -> None:
        """
        Render a file size error
        """
        font = "univers"
        error_message = (
            text2art("FILE TOO", font=font) + "\n\n" + text2art("LARGE", font=font)
        )
        self.text = error_message


class DataTableWindow(DataTable, BaseCodeWindow):
    """
    A DataTable widget for displaying code.
    """

    def refresh_from_file(self, file_path: pathlib.Path) -> None:
        """
        Load a file into a DataTable
        """
        if ".csv" in file_path.suffixes:
            df = pd.read_csv(file_path, nrows=1000)
        elif file_path.suffix.lower() in [".parquet"]:
            df = pd.read_parquet(file_path)
        elif file_path.suffix.lower() in [".feather", ".fea"]:
            df = pd.read_feather(file_path)
        else:
            msg = f"Cannot render file as a DataTable, {file_path}."
            raise NotImplementedError(msg)
        self.refresh_from_df(df)

    def refresh_from_df(
        self,
        pandas_dataframe: pd.DataFrame,
        show_index: bool = True,
        index_name: str | None = None,
    ) -> None:
        """
        Convert a pandas.DataFrame obj into a rich.Table obj.

        Parameters
        ----------
        pandas_dataframe: pd.DataFrame
            A Pandas DataFrame to be converted to a rich Table.
        show_index: bool
            Add a column with a row count to the table. Defaults to True.
        index_name: Optional[str]
            The column name to give to the index column.
            Defaults to None, showing no value.

        Returns
        -------
        DataTableWindow[str]
            The DataTable instance passed, populated with the DataFrame values.
        """
        self.clear(columns=True)
        if show_index:
            index_name = str(index_name) if index_name else ""
            self.add_column(index_name)
        for column in pandas_dataframe.columns:
            self.add_column(str(column))
        pandas_dataframe.replace([np.NaN], [""], inplace=True)
        for index, value_list in enumerate(pandas_dataframe.values.tolist()):
            row = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            self.add_row(*row)


class WindowSwitcher(Container):
    """
    A container that contains the file content windows
    """

    show_tree = var(True)

    datatable_extensions: ClassVar[list[str]] = [".csv", ".parquet", ".feather", ".fea"]
    image_extensions: ClassVar[list[str]] = image_file_extensions.copy()
    markdown_extensions: ClassVar[list[str]] = [".md"]
    json_extensions: ClassVar[list[str]] = [".json"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.static_window = StaticWindow()
        self.datatable_window = DataTableWindow(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.datatable_window.display = False
        self.text_area = TextAreaWindow(
            theme="monokai", soft_wrap=False, show_line_numbers=True
        )

    def compose(self) -> ComposeResult:
        """
        Compose the widget
        """
        yield self.static_window
        yield self.datatable_window
        yield self.text_area

    def switch_window(self, window: BaseCodeWindow) -> None:
        """
        Switch to the window
        """
        windows = list(self.compose())
        for window_screen in windows:
            if window is window_screen:
                window_screen.display = True
                window_screen.focus()
            else:
                window_screen.display = False

    def render_file(self, file_path: pathlib.Path, scroll_home: bool = True) -> None:
        """
        Render a file
        """
        switch_window = self.static_window
        if file_path.suffix in self.datatable_extensions:
            self.datatable_window.refresh_from_file(file_path=file_path)
            switch_window = self.datatable_window
        elif file_path.suffix in self.image_extensions:
            image = self.static_window.file_to_image(file_path=file_path)
            self.static_window.update(image)
        elif file_path.suffix in self.markdown_extensions:
            markdown = self.static_window.file_to_markdown(file_path=file_path)
            self.static_window.update(markdown)
        elif file_path.suffix in self.json_extensions:
            json_str = self.static_window.file_to_json(file_path=file_path)
            self.text_area.language = "json"
            self.text_area.text = json_str
            switch_window = self.text_area
        else:
            string = self.static_window.file_to_string(file_path=file_path)
            self.text_area.text = string
            self.text_area.language = self.text_area.language_mapping.get(
                file_path.suffix.lower(), "regex"
            )
            switch_window = self.text_area
        if scroll_home:
            switch_window.scroll_home(animate=False)
        self.switch_window(switch_window)

    def action_toggle_files(self) -> None:
        """
        Called in response to key binding.
        """
        self.show_tree = not self.show_tree
        if not self.show_tree:
            self.focus()

    def watch_show_tree(self, show_tree: bool) -> None:
        """
        Called when show_tree is modified.
        """
        self.set_class(show_tree, "-show-tree")
