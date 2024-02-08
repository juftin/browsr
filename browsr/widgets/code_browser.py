"""
The Primary Content Container
"""

from __future__ import annotations

import inspect
import json
import pathlib
import shutil
from textwrap import dedent
from typing import Any, ClassVar

import numpy as np
import pandas as pd
import pyperclip
import upath
from art import text2art
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich_pixels import Pixels
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.events import Mount
from textual.reactive import var
from textual.widgets import DataTable, DirectoryTree, Static
from textual_universal_directorytree import is_local_path, is_remote_path

from browsr.base import (
    TextualAppContext,
)
from browsr.config import favorite_themes, image_file_extensions
from browsr.exceptions import FileSizeError
from browsr.utils import (
    ArchiveFileError,
    FileInfo,
    get_file_info,
    handle_duplicate_filenames,
    open_image,
    render_file_to_string,
)
from browsr.widgets.confirmation import ConfirmationPopUp, ConfirmationWindow
from browsr.widgets.double_click_directory_tree import DoubleClickDirectoryTree
from browsr.widgets.files import CurrentFileInfoBar
from browsr.widgets.universal_directory_tree import (
    BrowsrDirectoryTree,
)
from browsr.widgets.vim import VimDataTable, VimScroll


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
    linenos = var(False)
    rich_themes = favorite_themes
    show_tree = var(True)
    force_show_tree = var(False)
    hidden_table_view = var(False)
    selected_file_path: upath.UPath | pathlib.Path | None | var[None] = var(None)

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="f", action="toggle_files", description="Files"),
        Binding(key="t", action="theme", description="Theme"),
        Binding(key="n", action="linenos", description="Line Numbers"),
        Binding(key="r", action="reload", description="Reload"),
        Binding(key=".", action="parent_dir", description="Parent Directory"),
    ]

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
        self.code_view = VimScroll(Static(id="code", expand=True), id="code-view")
        self.table_view: DataTable[str] = VimDataTable(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.table_view.display = False
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
        yield self.code_view
        yield self.table_view
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

    def action_toggle_files(self) -> None:
        """
        Called in response to key binding.
        """
        self.show_tree = not self.show_tree

    def watch_show_tree(self, show_tree: bool) -> None:
        """
        Called when show_tree is modified.
        """
        self.set_class(show_tree, "-show-tree")

    def action_parent_dir(self) -> None:
        """
        Go to the parent directory
        """
        new_path = self.config_object.path.parent.resolve()
        if new_path != self.config_object.path:
            self.config_object.file_path = str(new_path)
            self.directory_tree.path = new_path
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
        if self.selected_file_path is None:
            return
        elif self.theme_index < len(self.rich_themes) - 1:
            self.theme_index += 1
        else:
            self.theme_index = 0
        self.render_code_page(file_path=self.selected_file_path, scroll_home=False)

    def action_linenos(self) -> None:
        """
        An action to toggle line numbers.
        """
        if self.selected_file_path is None:
            return
        self.linenos = not self.linenos
        self.render_code_page(file_path=self.selected_file_path, scroll_home=False)

    def action_reload(self) -> None:
        """
        Refresh the directory.
        """
        self.directory_tree.reload()
        self.notify(
            title="Directory Reloaded",
            message=str(self.directory_tree.path),
            severity="information",
            timeout=1,
        )

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
        self.render_code_page(file_path=upath.UPath(message.path))
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

    def render_code_page(
        self,
        file_path: pathlib.Path,
        scroll_home: bool = True,
        content: Any | None = None,
    ) -> None:
        """
        Render the Code Page with Rich Syntax
        """
        code_view = self.query_one("#code", Static)
        font = "univers"
        if content is not None:
            code_view.update(text2art(content, font=font))
            return
        element = self._render_file(file_path=file_path, code_view=code_view, font=font)
        if isinstance(element, DataTable):
            self.code_view.display = False
            self.table_view.display = True
            if self.code_view.has_focus:
                self.table_view.focus()
            if scroll_home is True:
                self.query_one(DataTable).scroll_home(animate=False)
        elif element is not None:
            self.table_view.display = False
            self.code_view.display = True
            if self.table_view.has_focus:
                self.code_view.focus()
            code_view.update(element)
            if scroll_home is True:
                self.query_one("#code-view").scroll_home(animate=False)
            theme_name = self.rich_themes[self.theme_index]
            self.app.sub_title = f"{file_path} [{theme_name}]"

    def render_document(
        self,
        file_info: FileInfo,
    ) -> Syntax | Markdown | DataTable[str] | Pixels:
        """
        Render a Code Doc Given Its Extension

        Parameters
        ----------
        file_info: FileInfo
            The file info object for the file to render.

        Returns
        -------
        Union[Syntax, Markdown, DataTable[str], Pixels]
        """
        document = file_info.file
        if document.suffix == ".md":
            return Markdown(
                document.read_text(encoding="utf-8"),
                code_theme=self.rich_themes[self.theme_index],
                hyperlinks=True,
            )
        elif ".csv" in document.suffixes:
            df = pd.read_csv(document, nrows=1000)
            return self.df_to_table(pandas_dataframe=df, table=self.table_view)
        elif document.suffix == ".parquet":
            df = pd.read_parquet(document)[:1000]
            return self.df_to_table(pandas_dataframe=df, table=self.table_view)
        elif document.suffix.lower() in [".feather", ".fea"]:
            df = pd.read_feather(document)[:1000]
            return self.df_to_table(pandas_dataframe=df, table=self.table_view)
        elif document.suffix.lower() in image_file_extensions:
            screen_width = self.app.size.width / 4
            content = open_image(document=document, screen_width=screen_width)
            return content
        elif document.suffix.lower() in [".json"]:
            code_str = render_file_to_string(file_info=file_info)
            try:
                code_obj = json.loads(code_str)
                code_lines = json.dumps(code_obj, indent=2).splitlines()
            except json.JSONDecodeError:
                code_lines = code_str.splitlines()
        else:
            code_str = render_file_to_string(file_info=file_info)
            code_lines = code_str.splitlines()
        code = "\n".join(code_lines[:1000])
        lexer = Syntax.guess_lexer(str(document), code=code)
        return Syntax(
            code=code,
            lexer=lexer,
            line_numbers=self.linenos,
            word_wrap=False,
            indent_guides=False,
            theme=self.rich_themes[self.theme_index],
        )

    @staticmethod
    def df_to_table(
        pandas_dataframe: pd.DataFrame,
        table: DataTable[str],
        show_index: bool = True,
        index_name: str | None = None,
    ) -> DataTable[str]:
        """
        Convert a pandas.DataFrame obj into a rich.Table obj.

        Parameters
        ----------
        pandas_dataframe: pd.DataFrame
            A Pandas DataFrame to be converted to a rich Table.
        table: DataTable[str]
            A DataTable that should be populated by the DataFrame values.
        show_index: bool
            Add a column with a row count to the table. Defaults to True.
        index_name: Optional[str]
            The column name to give to the index column.
            Defaults to None, showing no value.

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

    def _render_file(
        self, file_path: pathlib.Path, code_view: Static, font: str
    ) -> Syntax | Markdown | DataTable[str] | Pixels | None:
        """
        Render a File
        """
        rich_theme = self.rich_themes[self.theme_index]
        try:
            file_info = get_file_info(file_path=file_path)
            self._handle_file_size(file_info=file_info)
            element = self.render_document(file_info=file_info)
            return element
        except FileSizeError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("FILE TOO", font=font) + "\n\n" + text2art("LARGE", font=font)
            )
            self.sub_title = f"ERROR [{rich_theme}]"
        except PermissionError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("PERMISSION", font=font)
                + "\n\n"
                + text2art("ERROR", font=font)
            )
            self.sub_title = f"ERROR [{rich_theme}]"
        except UnicodeError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("ENCODING", font=font) + "\n\n" + text2art("ERROR", font=font)
            )
            self.sub_title = f"ERROR [{rich_theme}]"
        except ArchiveFileError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("ARCHIVE", font=font) + "\n\n" + text2art("FILE", font=font)
            )
            self.sub_title = f"ERROR [{rich_theme}]"
        except Exception:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(Traceback(theme=rich_theme, width=None))
            self.sub_title = "ERROR" + f" [{rich_theme}]"
        return None

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

    def _handle_file_size(self, file_info: FileInfo) -> None:
        """
        Handle a File Size
        """
        file_size_mb = file_info.size / 1000 / 1000
        too_large = file_size_mb >= self.config_object.max_file_size
        exception = (
            True
            if is_local_path(file_info.file) and ".csv" in file_info.file.suffixes
            else False
        )
        if too_large is True and exception is not True:
            raise FileSizeError("File too large")
