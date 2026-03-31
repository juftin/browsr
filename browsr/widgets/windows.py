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
    open_image,
)
from browsr.widgets.vim import VimDataTable, VimScroll


class FileToStringResult(NamedTuple):
    result: str
    error_occurred: bool


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
        elif isinstance(exception, FileNotFoundError):
            error_message = (
                text2art("FILE NOT", font=font) + "\n\n" + text2art("FOUND", font=font)
            )
        else:
            raise exception from exception
        return error_message


class StaticWindow(Static, BaseCodeWindow):
    """
    A static widget for displaying code.
    """

    theme: Reactive[str] = reactive(favorite_themes[0])
    rich_themes: ClassVar[list[str]] = favorite_themes

    def __init__(
        self, config_object: TextualAppContext, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config_object = config_object
        self.linenos = False

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


class TextWindow(TextArea, BaseCodeWindow):
    """
    A window that displays text using a TextArea.
    """

    linenos: Reactive[bool] = reactive(True)
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
        self.show_line_numbers = self.linenos
        self.soft_wrap = False
        self.display = False

    def watch_linenos(self, linenos: bool) -> None:
        """
        Called when linenos is modified.
        """
        self.show_line_numbers = linenos

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
                self.theme = "github_light"
                return
        target = textarea_theme_map.get(rich_theme, self.default_theme)
        if target in self.available_themes:
            self.theme = target

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


class WindowSwitcher(Container):
    """
    A container that contains the file content windows
    """

    show_tree: Reactive[bool] = reactive(True)
    linenos: Reactive[bool] = reactive(False, init=False)

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
        self.theme = favorite_themes[0]
        self.static_window = StaticWindow(expand=True, config_object=config_object)
        self.text_window = TextWindow()
        self.datatable_window = DataTableWindow(
            zebra_stripes=True, show_header=True, show_cursor=True, id="table-view"
        )
        self.datatable_window.display = False
        self.vim_scroll = VimScroll(self.static_window)
        # Apply initial state
        self.static_window.theme = self.theme
        self.text_window.linenos = self.linenos
        self.text_window.theme = self.text_window.default_theme

    def watch_linenos(self, linenos: bool) -> None:
        """
        Called when linenos is modified.
        """
        self.static_window.linenos = linenos
        self.text_window.linenos = linenos
        if isinstance(self.static_window.content, Syntax):
            self.static_window.content.line_numbers = linenos
            self.static_window.refresh()

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

    def watch_theme(self, theme: str) -> None:
        """
        Called when theme is modified.
        """
        self.theme = theme
        self.static_window.theme = theme
        if self.text_window.display:
            self.text_window.apply_smart_theme(theme)
        self._update_subtitle()

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
        screens: dict[Widget, Widget] = {
            self.static_window: self.vim_scroll,
            self.text_window: self.text_window,
            self.datatable_window: self.datatable_window,
        }
        for window_screen, _ in screens.items():
            if window is window_screen:
                screens[window_screen].display = True
            else:
                screens[window_screen].display = False
        if window is self.text_window:
            # We only apply the smart theme if it's currently using a non-standard theme
            # or if it's the first time it's being shown.
            # But the user wants vscode_dark to persist.
            pass
        self._update_subtitle()

    def render_file(self, file_path: UPath, scroll_home: bool = True) -> None:
        """
        Render a file
        """
        switch_window: BaseCodeWindow = self.static_window
        joined_suffixes = "".join(file_path.suffixes).lower()
        if joined_suffixes in self.datatable_extensions:
            self.datatable_window.refresh_from_file(
                file_path=file_path, max_lines=self.config_object.max_lines
            )
            switch_window = self.datatable_window
        elif file_path.suffix.lower() in self.image_extensions:
            image = self.static_window.file_to_image(file_path=file_path)
            self.static_window.update(image)
        elif file_path.suffix.lower() in self.markdown_extensions:
            markdown = self.static_window.file_to_markdown(
                file_path=file_path, max_lines=self.config_object.max_lines
            )
            self.static_window.update(markdown)
        elif file_path.suffix.lower() in self.json_extensions:
            json_str = self.static_window.file_to_json(
                file_path=file_path, max_lines=self.config_object.max_lines
            )
            self.text_window.load_text(json_str)
            self.text_window.detect_language(file_path)
            switch_window = self.text_window
        else:
            result = self.static_window.file_to_string(
                file_path=file_path, max_lines=self.config_object.max_lines
            )
            if result.error_occurred:
                self.static_window.update(result.result)
                switch_window = self.static_window
            else:
                self.text_window.load_text(result.result)
                self.text_window.detect_language(file_path)
                switch_window = self.text_window
        self.switch_window(switch_window)
        active_widget = self.get_active_widget()
        if scroll_home:
            if active_widget is self.vim_scroll:
                self.vim_scroll.scroll_home(animate=False)
            else:
                switch_window.scroll_home(animate=False)
        self.rendered_file = file_path
        self._update_subtitle()

    def next_theme(self) -> str | None:
        """
        Switch to the next theme
        """
        active_widget = self.get_active_widget()
        if active_widget is self.text_window:
            themes = list(textarea_theme_map.values())
            # Ensure uniqueness while preserving order
            unique_themes = []
            for t in themes:
                if t not in unique_themes:
                    unique_themes.append(t)
            try:
                current_index = unique_themes.index(self.text_window.theme)
            except ValueError:
                current_index = -1
            next_theme = unique_themes[(current_index + 1) % len(unique_themes)]
            self.text_window.theme = next_theme
            self._update_subtitle()
            return next_theme
        if active_widget is self.vim_scroll:
            try:
                current_index = favorite_themes.index(self.theme)
            except ValueError:
                current_index = -1
            next_theme_rich = favorite_themes[
                (current_index + 1) % len(favorite_themes)
            ]
            self.watch_theme(next_theme_rich)
            return next_theme_rich

        return None

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
