"""
Code browser example.

Run with:
    python code_browser.py PATH
"""

import json
import pathlib
from os import getenv
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Union

import click
import pandas as pd
import rich_click
import rich_pixels
import upath
from art import text2art  # type: ignore[import]
from PIL import Image
from rich import traceback
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.traceback import Traceback
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

rich_click.rich_click.MAX_WIDTH = 100
rich_click.rich_click.STYLE_OPTION = "bold green"
rich_click.rich_click.STYLE_SWITCH = "bold blue"
rich_click.rich_click.STYLE_METAVAR = "bold red"
rich_click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold blue"
rich_click.rich_click.STYLE_HELPTEXT = ""
rich_click.rich_click.STYLE_HEADER_TEXT = "bold green"
rich_click.rich_click.STYLE_OPTION_DEFAULT = "bold yellow"
rich_click.rich_click.STYLE_OPTION_HELP = ""
rich_click.rich_click.STYLE_ERRORS_SUGGESTION = "bold red"
rich_click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE_HEAVY"
rich_click.rich_click.STYLE_COMMANDS_TABLE_BOX = "SIMPLE_HEAVY"

favorite_themes: List[str] = [
    "monokai",
    "material",
    "dracula",
    "solarized-light",
    "one-dark",
    "solarized-dark",
    "emacs",
    "vim",
    "github-dark",
    "native",
    "paraiso-dark",
]

rich_default_theme = getenv("RICH_THEME", None)
if rich_default_theme in favorite_themes:
    assert isinstance(rich_default_theme, str)
    favorite_themes.remove(rich_default_theme)
if rich_default_theme is not None:
    assert isinstance(rich_default_theme, str)
    favorite_themes.insert(0, rich_default_theme)


class CodeBrowser(BrowsrTextualApp):
    """
    Textual code browser app.
    """

    CSS_PATH = "code_browser.css"
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
    ) -> Union[Syntax, Markdown, DataTable[str]]:
        """
        Render a Code Doc Given Its Extension

        Parameters
        ----------
        document: pathlib.Path
            File Path to Render

        Returns
        -------
        Union[Syntax, Markdown, DataTable[str]]
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
        elif document.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            screen_width = self.app.size.width / 4
            with Image.open(document) as image:
                image_width = image.width
                image_height = image.height
                size_ratio = image_width / screen_width
                new_width = min(int(image_width / size_ratio), image_width)
                new_height = min(int(image_height / size_ratio), image_height)
                resized = image.resize((new_width, new_height))
                content = rich_pixels.Pixels.from_image(resized)
            return content
        elif document.suffix.lower() in [".json"]:
            code_str = document.read_text()
            code_obj = json.loads(code_str)
            code_lines = json.dumps(code_obj, indent=2).splitlines()
        else:
            code_lines = document.read_text().splitlines()
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
            self.render_code_page(file_path=pathlib.Path.cwd(), content="BROWSR")

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


@click.command(name="browse", cls=rich_click.rich_command.RichCommand)
@click.argument("path", default=None, required=False, metavar="PATH")
@click.pass_obj
@debug_option
def browse(
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
    browse()
