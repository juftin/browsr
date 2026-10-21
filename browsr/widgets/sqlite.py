"""SQLite table selection and paged data."""

from __future__ import annotations

import sqlite3
from typing import Any, ClassVar

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal
from textual.widgets import Button, DataTable, Select, Static
from textual_universal_directorytree import UPath

from browsr.sqlite import SQLiteDatabase
from browsr.widgets.vim import vim_cursor_bindings

BLOB_PREVIEW_BYTES = 32


class SQLiteDataTable(DataTable[Text]):
    """Display literal SQLite values with the browser's Vim navigation."""

    BINDINGS: ClassVar[list[BindingType]] = [
        *DataTable.BINDINGS,
        *vim_cursor_bindings,
    ]


class SQLiteWindow(Container):
    """A read-only SQLite viewer using the browser's normal navigation keys."""

    can_focus = True
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+left", "previous_page", "Previous Page"),
        Binding("ctrl+right", "next_page", "Next Page"),
        Binding("ctrl+up", "previous_table", "Previous Table"),
        Binding("ctrl+down", "next_table", "Next Table"),
    ]
    DEFAULT_CSS = """
    SQLiteWindow { height: 100%; }
    SQLiteWindow .sqlite-toolbar { height: 3; }
    SQLiteWindow Select { width: 1fr; }
    SQLiteWindow Button { min-width: 10; width: auto; }
    SQLiteWindow SQLiteDataTable { height: 1fr; }
    SQLiteWindow .sqlite-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.database: SQLiteDatabase | None = None
        self.table_name: str | None = None
        self.row_offset = 0
        self.page_size = 1000
        self.has_next = False
        self.selector: Select[str] = Select([], prompt="Select a table or view")
        self.previous_button = Button("Previous", id="sqlite-previous", disabled=True)
        self.next_button = Button("Next", id="sqlite-next", disabled=True)
        self.data_table = SQLiteDataTable(zebra_stripes=True, id="sqlite-data")
        self.status = Static("", classes="sqlite-status", markup=False)
        self.display = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="sqlite-toolbar"):
            yield self.selector
            yield self.previous_button
            yield self.next_button
        yield self.data_table
        yield self.status

    def refresh_from_file(self, file_path: UPath, max_lines: int = 1000) -> None:
        """Load a database, resetting the selection and any stale results."""
        self.close()
        self.page_size = max(1, max_lines)
        self.data_table.clear(columns=True)
        self.selector.set_options([])
        self.selector.disabled = True
        self._update_buttons()
        try:
            self.database = SQLiteDatabase(file_path)
        except (sqlite3.Error, OSError, ValueError) as error:
            self.status.update(f"Unable to open SQLite database: {error}")
            return
        objects = self.database.objects
        if not objects:
            self.status.update("This SQLite database has no user tables or views.")
            return
        self.selector.set_options(
            [(Text(f"{item.name} ({item.kind})"), item.name) for item in objects]
        )
        self.selector.disabled = False
        self.selector.value = objects[0].name
        self.select_table(objects[0].name)

    @on(Select.Changed)
    def table_changed(self, event: Select.Changed) -> None:
        """Switch tables without allowing queued events to restore old selections."""
        event.stop()
        if (
            isinstance(event.value, str)
            and event.value == self.selector.value
            and event.value != self.table_name
        ):
            self.select_table(event.value)

    def select_table(self, name: str) -> None:
        """Reset paging and display the selected object's data."""
        if self.database is None:
            return
        selected = next(
            (item for item in self.database.objects if item.name == name), None
        )
        if selected is None:
            return
        self.table_name = name
        self.row_offset = 0
        self._load_page()

    @staticmethod
    def _format_value(value: Any) -> Text:
        """Render values literally, preserving NULL, BLOBs, and Rich-like text."""
        if value is None:
            return Text("NULL", style="dim italic")
        if isinstance(value, bytes):
            preview = value[:BLOB_PREVIEW_BYTES].hex()
            suffix = "…" if len(value) > BLOB_PREVIEW_BYTES else ""
            return Text(f"BLOB ({len(value)} bytes): {preview}{suffix}")
        return Text(str(value))

    def _load_page(self) -> None:
        """Fetch a bounded page, reporting SQL errors inside the viewer."""
        self.data_table.clear(columns=True)
        self.has_next = False
        if self.database is None or self.table_name is None:
            return
        try:
            page = self.database.read_page(
                self.table_name, self.row_offset, self.page_size
            )
            self.data_table.add_columns(*(Text(name) for name in page.columns))
            for row in page.rows:
                self.data_table.add_row(*(self._format_value(value) for value in row))
            self.has_next = page.has_next
            if page.rows:
                start, end = self.row_offset + 1, self.row_offset + len(page.rows)
                self.status.update(
                    f"Read-only · {self.table_name} · Rows {start}-{end}"
                )
            else:
                self.status.update(f"Read-only · {self.table_name} · No rows")
        except (sqlite3.Error, ValueError) as error:
            self.status.update(f"Unable to read {self.table_name}: {error}")
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.previous_button.disabled = self.row_offset == 0
        self.next_button.disabled = not self.has_next

    @on(Button.Pressed, "#sqlite-previous")
    def previous_page(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_previous_page()

    @on(Button.Pressed, "#sqlite-next")
    def next_page(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_next_page()

    def action_previous_page(self) -> None:
        """Show the previous page."""
        if self.row_offset > 0:
            self.row_offset = max(0, self.row_offset - self.page_size)
            self._load_page()

    def action_next_page(self) -> None:
        """Show the next page when the lookahead found more rows."""
        if self.has_next:
            self.row_offset += self.page_size
            self._load_page()

    def _change_table(self, direction: int) -> None:
        """Cycle through the dropdown's tables and views without moving focus."""
        if self.database is None or not self.database.objects:
            return
        names = [item.name for item in self.database.objects]
        if self.table_name in names:
            index = (names.index(self.table_name) + direction) % len(names)
        else:
            index = 0 if direction > 0 else -1
        name = names[index]
        self.selector.value = name
        if name != self.table_name:
            self.select_table(name)

    def action_previous_table(self) -> None:
        """Show the previous table, wrapping to the last at the beginning."""
        self._change_table(-1)

    def action_next_table(self) -> None:
        """Show the next table, wrapping to the first at the end."""
        self._change_table(1)

    def close(self) -> None:
        """Release resources when switching files or leaving the app."""
        if self.database is not None:
            self.database.close()
            self.database = None
        self.table_name = None
        self.row_offset = 0
        self.has_next = False

    def on_unmount(self) -> None:
        self.close()
