"""
Content Windows
"""

from __future__ import annotations

import contextlib
from json import JSONDecodeError
from typing import Any, ClassVar, NamedTuple

import orjson
import pandas as pd
import pyperclip
from art import text2art
from numpy import nan
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich_pixels import Pixels
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Static, TextArea
from textual_universal_directorytree import UPath

from browsr.base import TextualAppContext
from browsr.config import (
    favorite_themes,
    filename_map,
    image_file_extensions,
    language_map,
    textarea_default_theme,
    textarea_theme_map,
)
from browsr.exceptions import FileSizeError
from browsr.utils import (
    ArchiveFileError,
    FileInfo,
    get_file_info,
    open_image,
)
from browsr.widgets.vim import VimDataTable, VimScroll


class FileToStringResult(NamedTuple):
    result: str
    error_occurred: bool


class ThemeVisibleMixin:
    """
    Mixin for widgets with a theme
    """

    theme: Reactive[str] = reactive(favorite_themes[0])


class LinenosVisibleMixin:
    """
    Mixin for widgets with line numbers
    """

    linenos: Reactive[bool] = reactive(False)


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

    def file_to_string(
        self, file_path: UPath, max_lines: int | None = None
    ) -> FileToStringResult:
        """
        Load a file into a string

        Returns a tuple of the string and a boolean indicating if an exception occurred.
        """
        error_occurred = False
        try:
            if file_path.suffix in self.archive_extensions:
                message = f"Cannot render archive file {file_path}."
                raise ArchiveFileError(message)
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            text = self.handle_exception(exception=e)
            error_occurred = True
        if max_lines:
            text = "\n".join(text.split("\n")[:max_lines])
        return FileToStringResult(result=text, error_occurred=error_occurred)

    def file_to_image(self, file_path: UPath) -> Pixels:
        """
        Load a file into an image
        """
        screen_width = self.app.size.width / 2
        content = open_image(document=file_path, screen_width=screen_width)
        return content

    def file_to_json(self, file_path: UPath, max_lines: int | None = None) -> str:
        """
        Load a file into a JSON object
        """
        code_str = self.file_to_string(file_path=file_path).result
        try:
            code_obj = orjson.loads(code_str)
            code_str = orjson.dumps(code_obj, option=orjson.OPT_INDENT_2).decode(
                "utf-8"
            )
        except JSONDecodeError:
            pass
        if max_lines:
            code_str = "\n".join(code_str.split("\n")[:max_lines])
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
        """
        font = "univers"
        exception_map = {
            ArchiveFileError: ("ARCHIVE", "FILE"),
            FileSizeError: ("FILE TOO", "LARGE"),
            PermissionError: ("PERMISSION", "ERROR"),
            UnicodeError: ("ENCODING", "ERROR"),
            FileNotFoundError: ("FILE NOT", "FOUND"),
        }
        for exc_type, (line1, line2) in exception_map.items():
            if isinstance(exception, exc_type):
                return text2art(line1, font=font) + "\n\n" + text2art(line2, font=font)
        raise exception from exception


class StaticWindow(Static, BaseCodeWindow, ThemeVisibleMixin, LinenosVisibleMixin):
    """
    A static widget for displaying code.
    """

    rich_themes: ClassVar[list[str]] = favorite_themes

    def __init__(
        self, config_object: TextualAppContext, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_object = config_object

    def file_to_markdown(
        self, file_path: UPath, max_lines: int | None = None
    ) -> Markdown:
        """
        Load a file into a Markdown
        """
        return Markdown(
            self.file_to_string(file_path, max_lines=max_lines).result,
            code_theme=self.theme,
            hyperlinks=True,
        )

    def text_to_syntax(self, text: str, file_path: str | UPath) -> Syntax:
        """
        Convert text to syntax
        """
        lexer = Syntax.guess_lexer(str(file_path), code=text)
        return Syntax(
            code=text,
            lexer=lexer,
            line_numbers=self.linenos,
            word_wrap=False,
            indent_guides=False,
            theme=self.theme,
        )

    def watch_linenos(self, linenos: bool) -> None:
        """
        Called when linenos is modified.
        """
        if isinstance(self.content, Syntax):
            self.content.line_numbers = linenos
            self.refresh()

    def watch_theme(self, theme: str) -> None:
        """
        Called when theme is modified.
        """
        if isinstance(self.content, Syntax):
            updated_syntax = Syntax(
                code=self.content.code,
                lexer=self.content.lexer,
                line_numbers=self.content.line_numbers,
                word_wrap=False,
                indent_guides=False,
                theme=theme,
            )
            self.update(updated_syntax)
        elif isinstance(self.content, Markdown):
            self.content.code_theme = self.theme


class TextWindow(TextArea, BaseCodeWindow, ThemeVisibleMixin, LinenosVisibleMixin):
    """
    A window that displays text using a TextArea.
    """

    theme: Reactive[str] = reactive(textarea_default_theme)
    default_theme: ClassVar[str] = textarea_default_theme

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("l", "cursor_right", "Right", show=False),
        Binding("h", "cursor_left", "Left", show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(read_only=True, **kwargs)
        self.theme = self.default_theme
        self.soft_wrap = False
        self.display = False

    def watch_linenos(self, linenos: bool) -> None:
        """
        Called when linenos is modified.
        """
        before_scroll = self.scroll_x, self.scroll_y
        self.show_line_numbers = linenos
        self.scroll_to(x=before_scroll[0], y=before_scroll[1], animate=False)

    def copy_selected_text(self) -> None:
        """
        Copy the selected text to the clipboard.
        """
        if self.selected_text:
            pyperclip.copy(self.selected_text)
            self.app.notify(
                title="Copied",
                message="Selected text copied to clipboard",
                severity="information",
                timeout=1,
            )
        else:
            self.app.notify(
                title="No Selection",
                message="No text selected to copy",
                severity="warning",
                timeout=1,
            )

    def apply_smart_theme(self, rich_theme: str) -> None:
        """
        Apply a theme to the TextArea
        """
        with contextlib.suppress(RuntimeError, AttributeError):
            if not getattr(self.app, "dark", True):
                if self.theme != "github_light":
                    self.theme = "github_light"
                return
        target = textarea_theme_map.get(rich_theme, self.default_theme)
        if target in self.available_themes and self.theme != target:
            self.theme = target

    def load_file(self, text: str, file_path: UPath) -> None:
        """
        Load text and detect language
        """
        self.load_text(text)
        self.detect_language(file_path)

    def detect_language(self, file_path: str | UPath) -> None:
        """
        Detect the language from the file path
        """
        if isinstance(file_path, str):
            file_path = UPath(file_path)
        file_name = file_path.name.lower()
        if file_name in filename_map:
            self.language = filename_map[file_name]
            return
        ext = file_path.suffix.lstrip(".").lower()
        if ext in language_map:
            self.language = language_map[ext]
        elif ext in self.available_languages:
            self.language = ext
        else:
            self.language = None


class DataTableWindow(VimDataTable, BaseCodeWindow):
    """
    A DataTable widget for displaying code.
    """

    def refresh_from_file(self, file_path: UPath, max_lines: int | None = None) -> None:
        """
        Load a file into a DataTable
        """
        if ".csv" in file_path.suffixes:
            df = pd.read_csv(file_path, nrows=max_lines)
        elif file_path.suffix.lower() in [".parquet"]:
            df = pd.read_parquet(file_path).head(max_lines)
        elif file_path.suffix.lower() in [".feather", ".fea"]:
            df = pd.read_feather(file_path).head(max_lines)
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
        pandas_dataframe.replace([nan], [""], inplace=True)
        for index, value_list in enumerate(pandas_dataframe.values.tolist()):
            row = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            self.add_row(*row)


class WindowSwitcher(Container, ThemeVisibleMixin, LinenosVisibleMixin):
    """
    A container that contains the file content windows
    """

    show_tree: Reactive[bool] = reactive(True)

    datatable_extensions: ClassVar[list[str]] = [
        ".csv",
        ".parquet",
        ".feather",
        ".fea",
        ".csv.gz",
    ]
    image_extensions: ClassVar[list[str]] = image_file_extensions.copy()
    markdown_extensions: ClassVar[list[str]] = [".md"]
    json_extensions: ClassVar[list[str]] = [".json"]

    def __init__(
        self, config_object: TextualAppContext, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.rendered_file: UPath | None = None
        self.config_object = config_object
        self.static_window = StaticWindow(expand=True, config_object=config_object)
        self.text_window = TextWindow()
        self.datatable_window = DataTableWindow(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.datatable_window.display = False
        self.vim_scroll = VimScroll(self.static_window)

    def watch_linenos(self, linenos: bool) -> None:
        """
        Called when linenos is modified.
        """
        self.static_window.linenos = linenos
        self.text_window.linenos = linenos

    def watch_theme(self, theme: str) -> None:
        """
        Called when theme is modified.
        """
        self.static_window.theme = theme
        if self.text_window.display:
            self.text_window.apply_smart_theme(theme)
        self._update_subtitle()

    def _update_subtitle(self) -> None:
        """
        Update the app subtitle
        """
        if self.rendered_file is None:
            return
        active_widget = self.get_active_widget()
        if active_widget is self.text_window:
            display_theme = self.text_window.theme.replace("_", "-")
        elif active_widget is self.vim_scroll:
            display_theme = self.static_window.theme
        else:
            self.app.sub_title = str(self.rendered_file)
            return
        self.app.sub_title = str(self.rendered_file) + f" [{display_theme}]"

    def watch_dark(self, _dark: bool) -> None:
        """
        Called when dark mode is modified.
        """
        self.text_window.apply_smart_theme(self.theme)
        self.static_window.refresh()
        self._update_subtitle()

    def compose(self) -> ComposeResult:
        """
        Compose the widget
        """
        yield self.vim_scroll
        yield self.text_window
        yield self.datatable_window

    def get_active_widget(self) -> Widget:  # type: ignore[return]
        """
        Get the active widget
        """
        if self.vim_scroll.display:
            return self.vim_scroll
        elif self.text_window.display:
            return self.text_window
        elif self.datatable_window.display:
            return self.datatable_window

    def switch_window(self, window: BaseCodeWindow) -> None:
        """
        Switch to the window
        """
        window_map: dict[Widget, Widget] = {
            self.static_window: self.vim_scroll,
            self.text_window: self.text_window,
            self.datatable_window: self.datatable_window,
        }
        for window_widget, container_widget in window_map.items():
            container_widget.display = window is window_widget
        self._update_subtitle()

    def render_file(self, file_path: UPath, scroll_home: bool = True) -> None:
        """
        Render a file
        """
        try:
            file_info = get_file_info(file_path=file_path)
            self.static_window.handle_file_size(
                file_info=file_info, max_file_size=self.config_object.max_file_size
            )
            joined_suffixes = "".join(file_path.suffixes).lower()
            if joined_suffixes in self.datatable_extensions:
                switch_window = self._render_datatable(file_path)
            elif file_path.suffix.lower() in self.image_extensions:
                switch_window = self._render_image(file_path)
            elif file_path.suffix.lower() in self.markdown_extensions:
                switch_window = self._render_markdown(file_path)
            elif file_path.suffix.lower() in self.json_extensions:
                switch_window = self._render_json(file_path)
            else:
                switch_window = self._render_text(file_path)
        except Exception as e:
            error_message = self.static_window.handle_exception(exception=e)
            error_syntax = self.static_window.text_to_syntax(
                text=error_message,
                file_path=file_path,
            )
            self.static_window.update(error_syntax)
            switch_window = self.static_window

        self.switch_window(switch_window)
        active_widget = self.get_active_widget()
        if scroll_home:
            if active_widget is self.vim_scroll:
                self.vim_scroll.scroll_home(animate=False)
            else:
                switch_window.scroll_home(animate=False)
        self.rendered_file = file_path
        self._update_subtitle()

    def _render_datatable(self, file_path: UPath) -> BaseCodeWindow:
        """Render a datatable file"""
        self.datatable_window.refresh_from_file(
            file_path=file_path, max_lines=self.config_object.max_lines
        )
        return self.datatable_window

    def _render_image(self, file_path: UPath) -> BaseCodeWindow:
        """Render an image file"""
        image = self.static_window.file_to_image(file_path=file_path)
        self.static_window.update(image)
        return self.static_window

    def _render_markdown(self, file_path: UPath) -> BaseCodeWindow:
        """Render a markdown file"""
        markdown = self.static_window.file_to_markdown(
            file_path=file_path, max_lines=self.config_object.max_lines
        )
        self.static_window.update(markdown)
        return self.static_window

    def _render_json(self, file_path: UPath) -> BaseCodeWindow:
        """Render a JSON file"""
        json_str = self.static_window.file_to_json(
            file_path=file_path, max_lines=self.config_object.max_lines
        )
        self.text_window.load_file(json_str, file_path)
        return self.text_window

    def _render_text(self, file_path: UPath) -> BaseCodeWindow:
        """Render a text file"""
        result = self.static_window.file_to_string(
            file_path=file_path, max_lines=self.config_object.max_lines
        )
        if result.error_occurred:
            self.static_window.update(result.result)
            return self.static_window
        else:
            self.text_window.load_file(result.result, file_path)
            return self.text_window

    def next_theme(self) -> str | None:
        """
        Switch to the next theme
        """
        active_widget = self.get_active_widget()
        if active_widget is self.text_window:
            return self._next_textarea_theme()
        elif active_widget is self.vim_scroll:
            return self._next_rich_theme()
        return None

    def _next_textarea_theme(self) -> str:
        """Switch to the next TextArea theme"""
        themes = list(textarea_theme_map.values())
        unique_themes = list(dict.fromkeys(themes))
        try:
            current_index = unique_themes.index(self.text_window.theme)
        except ValueError:
            current_index = -1
        next_theme = unique_themes[(current_index + 1) % len(unique_themes)]
        self.text_window.theme = next_theme
        self._update_subtitle()
        return next_theme

    def _next_rich_theme(self) -> str:
        """Switch to the next Rich theme"""
        try:
            current_index = favorite_themes.index(self.theme)
        except ValueError:
            current_index = -1
        next_theme = favorite_themes[(current_index + 1) % len(favorite_themes)]
        self.theme = next_theme
        return next_theme

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
