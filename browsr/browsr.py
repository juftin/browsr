"""
Browsr TUI App

This module contains the code browser app for the browsr package.
This app was inspired by the CodeBrowser example from textual
"""

import json
import pathlib
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

import click
import pandas as pd
import rich_click
import upath
from art import text2art  # type: ignore[import]
from rich import traceback
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich_pixels import Pixels
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import DataTable, DirectoryTree, Footer, Header, Static
from upath.implementations.cloud import CloudPath

from browsr._base import (
    BrowsrClickContext,
    BrowsrTextualApp,
    FileSizeError,
    TextualAppContext,
    UniversalDirectoryTree,
    debug_option,
)
from browsr._config import favorite_themes, image_file_extensions
from browsr._utils import open_image
from browsr._version import __application__, __version__


class CodeBrowser(BrowsrTextualApp):
    """
    Textual code browser app.
    """

    TITLE = __application__
    CSS_PATH = "browsr.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "toggle_files", "Toggle Files"),
        ("t", "theme", "Toggle Theme"),
        ("n", "linenos", "Toggle Line Numbers"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    show_tree = var(True)
    theme_index = var(0)
    linenos = var(False)
    rich_themes = favorite_themes
    selected_file_path: Union[upath.UPath, pathlib.Path, None, var[None]] = var(None)
    force_show_tree = var(False)

    traceback.install(show_locals=True)

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
        self.directory_tree = UniversalDirectoryTree(str(file_path), id="tree-view")
        self.code_view = VerticalScroll(Static(id="code", expand=True), id="code-view")
        self.table_view: DataTable[str] = DataTable(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.table_view.display = False
        self.container = Container(self.directory_tree, self.code_view, self.table_view)
        yield self.container
        self.footer = Footer()
        yield self.footer

    def render_document(
        self,
        document: pathlib.Path,
    ) -> Union[Syntax, Markdown, DataTable[str], Pixels]:
        """
        Render a Code Doc Given Its Extension

        Parameters
        ----------
        document: pathlib.Path
            File Path to Render

        Returns
        -------
        Union[Syntax, Markdown, DataTable[str], Pixels]
        """
        if document.suffix == ".md":
            return Markdown(
                document.read_text(encoding="utf-8"),
                code_theme=self.rich_themes[self.theme_index],
                hyperlinks=True,
            )
        elif ".csv" in document.suffixes:
            df = pd.read_csv(document, nrows=500)
            return self.df_to_table(pandas_dataframe=df, table=self.table_view)
        elif document.suffix == ".parquet":
            df = pd.read_parquet(document)[:500]
            return self.df_to_table(pandas_dataframe=df, table=self.table_view)
        elif document.suffix.lower() in image_file_extensions:
            screen_width = self.app.size.width / 4
            content = open_image(document=document, screen_width=screen_width)
            return content
        elif document.suffix.lower() in [".json"]:
            code_str = document.read_text()
            code_obj = json.loads(code_str)
            code_lines = json.dumps(code_obj, indent=2).splitlines()
        else:
            code_lines = document.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
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

    @classmethod
    def _handle_file_size(cls, file_path: pathlib.Path) -> None:
        """
        Handle a File Size
        """
        stat = file_path.stat()
        if isinstance(stat, dict):
            file_size = {key.lower(): value for key, value in stat.items()}["size"]
            file_size_mb = file_size / 1000 / 1000
        else:
            file_size_mb = stat.st_size / 1000 / 1000
        max_file_size = 8
        too_large = file_size_mb >= max_file_size
        exception = (
            True
            if not isinstance(file_path, CloudPath) and ".csv" in file_path.suffixes
            else False
        )
        if too_large is True and exception is not True:
            raise FileSizeError("File too large")

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
        try:
            self._handle_file_size(file_path=file_path)
            element = self.render_document(document=file_path)
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
        except Exception:
            self.table_view.display = False
            self.code_view.display = True
            code_view.update(
                Traceback(theme=self.rich_themes[self.theme_index], width=None)
            )
            self.sub_title = "ERROR" + f" [{self.rich_themes[self.theme_index]}]"
        else:
            if isinstance(element, DataTable):
                self.code_view.display = False
                self.table_view.display = True
                if scroll_home is True:
                    self.query_one(DataTable).scroll_home(animate=False)
            else:
                self.table_view.display = False
                self.code_view.display = True
                code_view.update(element)
            if scroll_home is True:
                self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = f"{file_path} [{self.rich_themes[self.theme_index]}]"

    def on_mount(self) -> None:
        """
        On Application Mount - See If a File Should be Displayed
        """
        if self.selected_file_path is not None:
            self.show_tree = self.force_show_tree
            self.render_code_page(file_path=self.selected_file_path)
        else:
            self.show_tree = True
            self.render_code_page(
                file_path=pathlib.Path.cwd(), content=__application__.upper()
            )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """
        Called when the user click a file in the directory tree.
        """
        self.selected_file_path = upath.UPath(event.path)
        self.render_code_page(file_path=upath.UPath(event.path))

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


@click.command(name="browsr", cls=rich_click.rich_command.RichCommand)
@click.argument("path", default=None, required=False, metavar="PATH")
@click.version_option(version=__version__, prog_name=__application__)
@click.pass_obj
@debug_option
def browsr(
    context: Optional[BrowsrClickContext], path: Optional[str], debug: bool
) -> None:
    """
    Start the TUI File Browser

    This utility displays a TUI (textual user interface) application. The application
    allows you to visually browse through a repository and display the contents of its
    files
    """
    if context is None:
        context = BrowsrClickContext(debug=debug)
    elif context.debug is False:
        context.debug = debug
    config = TextualAppContext(file_path=path, debug=context.debug)
    app = CodeBrowser(config_object=config)
    app.run()


if __name__ == "__main__":
    browsr()
