"""
Browsr TUI App

This module contains the code browser app for the browsr package.
This app was inspired by the CodeBrowser example from textual
"""

import json
import pathlib
import shutil
from os import getenv
from textwrap import dedent
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, List, Optional, Union

import pandas as pd
import upath
from art import text2art  # type: ignore[import]
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich_pixels import Pixels
from textual import on
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal
from textual.events import Mount
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Header, Static
from textual_universal_directorytree import is_local_path, is_remote_path

from browsr._base import (
    BrowsrTextualApp,
    ConfirmationPopUp,
    CurrentFileInfoBar,
    FileSizeError,
    TextualAppContext,
    VimDataTable,
    VimScroll,
)
from browsr._config import favorite_themes, image_file_extensions
from browsr._utils import (
    ArchiveFileError,
    FileInfo,
    get_file_info,
    handle_duplicate_filenames,
    open_image,
    render_file_to_string,
)
from browsr._version import __application__
from browsr.universal_directory_tree import (
    BrowsrDirectoryTree,
)


class Browsr(BrowsrTextualApp):
    """
    Textual code browser app.
    """

    TITLE = __application__
    CSS_PATH = "browsr.css"
    BINDINGS: ClassVar[List[BindingType]] = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="f", action="toggle_files", description="Toggle Files"),
        Binding(key="t", action="theme", description="Toggle Theme"),
        Binding(key="n", action="linenos", description="Toggle Line Numbers"),
        Binding(key="d", action="toggle_dark", description="Toggle Dark Mode"),
    ]

    show_tree = var(True)
    theme_index = var(0)
    linenos = var(False)
    rich_themes = favorite_themes
    selected_file_path: Union[upath.UPath, pathlib.Path, None, var[None]] = var(None)
    force_show_tree = var(False)
    hidden_table_view = var(False)

    def watch_show_tree(self, show_tree: bool) -> None:
        """
        Called when show_tree is modified.
        """
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> Iterable[Widget]:
        """
        Compose our UI.
        """
        assert isinstance(self.config_object, TextualAppContext)
        file_path = self.config_object.path
        if is_remote_path(file_path):
            self.bind("x", "download_file", description="Download File", show=True)
        if file_path.is_file():
            self.selected_file_path = file_path
            file_path = file_path.parent
        elif file_path.is_dir() and file_path.joinpath("README.md").exists():
            if TYPE_CHECKING:
                assert isinstance(file_path, pathlib.Path)
            self.selected_file_path = file_path.joinpath("README.md")
            self.force_show_tree = True
        self.header = Header()
        yield self.header
        self.directory_tree = BrowsrDirectoryTree(str(file_path), id="tree-view")
        self.code_view = VimScroll(Static(id="code", expand=True), id="code-view")
        self.table_view: DataTable[str] = VimDataTable(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.table_view.display = False
        self.confirmation = ConfirmationPopUp()
        self.confirmation_window = Container(
            self.confirmation, id="confirmation-container"
        )
        self.confirmation_window.display = False
        self.container = Container(
            self.directory_tree,
            self.code_view,
            self.table_view,
            self.confirmation_window,
        )
        yield self.container
        self.file_information = CurrentFileInfoBar()
        self.info_bar = Horizontal(
            self.file_information,
            id="file-info-bar",
        )
        if self.selected_file_path is not None:
            self.file_information.file_info = get_file_info(
                file_path=self.selected_file_path
            )
        yield self.info_bar
        self.footer = Footer()
        yield self.footer

    def render_document(
        self,
        file_info: FileInfo,
    ) -> Union[Syntax, Markdown, DataTable[str], Pixels]:
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

    def _handle_file_size(self, file_info: FileInfo) -> None:
        """
        Handle a File Size
        """
        file_size_mb = file_info.size / 1000 / 1000
        too_large = file_size_mb >= self.config_object.max_file_size  # type: ignore[union-attr]
        exception = (
            True
            if is_local_path(file_info.file) and ".csv" in file_info.file.suffixes
            else False
        )
        if too_large is True and exception is not True:
            raise FileSizeError("File too large")

    def _render_file(
        self, file_path: pathlib.Path, code_view: Static, font: str
    ) -> Union[Syntax, Markdown, DataTable[str], Pixels, None]:
        """
        Render a File
        """
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
            self.sub_title = f"ERROR [{self.rich_themes[self.theme_index]}]"
        except PermissionError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("PERMISSION", font=font)
                + "\n\n"
                + text2art("ERROR", font=font)
            )
            self.sub_title = f"ERROR [{self.rich_themes[self.theme_index]}]"
        except UnicodeError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("ENCODING", font=font) + "\n\n" + text2art("ERROR", font=font)
            )
            self.sub_title = f"ERROR [{self.rich_themes[self.theme_index]}]"
        except ArchiveFileError:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                text2art("ARCHIVE", font=font) + "\n\n" + text2art("FILE", font=font)
            )
            self.sub_title = f"ERROR [{self.rich_themes[self.theme_index]}]"
        except Exception:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                Traceback(theme=self.rich_themes[self.theme_index], width=None)
            )
            self.sub_title = "ERROR" + f" [{self.rich_themes[self.theme_index]}]"
        return None

    def render_code_page(
        self,
        file_path: pathlib.Path,
        scroll_home: bool = True,
        content: Optional[Any] = None,
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
            self.sub_title = f"{file_path} [{self.rich_themes[self.theme_index]}]"

    @on(Mount)
    def start_up_app(self) -> None:
        """
        On Application Mount - See If a File Should be Displayed
        """
        if self.selected_file_path is not None:
            self.show_tree = self.force_show_tree
            self.render_code_page(file_path=self.selected_file_path)
            if self.show_tree is False and self.code_view.display is True:
                self.code_view.focus()
            elif self.show_tree is False and self.table_view.display is True:
                self.table_view.focus()
        else:
            self.show_tree = True
            self.render_code_page(
                file_path=pathlib.Path.cwd(), content=__application__.upper()
            )

    @on(BrowsrDirectoryTree.FileSelected)
    def handle_file_selected(self, message: BrowsrDirectoryTree.FileSelected) -> None:
        """
        Called when the user click a file in the directory tree.
        """
        self.selected_file_path = upath.UPath(message.path)
        file_info = get_file_info(file_path=self.selected_file_path)
        self.render_code_page(file_path=upath.UPath(message.path))
        self.file_information.file_info = file_info

    def action_toggle_files(self) -> None:
        """
        Called in response to key binding.
        """
        self.show_tree = not self.show_tree

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

    def _get_download_file_name(self) -> pathlib.Path:
        """
        Get the download file name.
        """
        download_dir = pathlib.Path.home() / "Downloads"
        if not download_dir.exists():
            raise FileNotFoundError(f"Download directory {download_dir} not found")
        download_path = download_dir / self.selected_file_path.name  # type: ignore[union-attr]
        handled_download_path = handle_duplicate_filenames(file_path=download_path)
        return handled_download_path

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

    def action_download_file(self) -> None:
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


app = Browsr(
    config_object=TextualAppContext(file_path=getenv("BROWSR_PATH"), debug=True)
)

if __name__ == "__main__":
    app.run()
