"""
Shortcuts Widget
"""

from __future__ import annotations

from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.widgets import Button, DataTable, Static

from browsr.widgets.base import BaseOverlay, BasePopUp


class ShortcutsPopUp(BasePopUp):
    """A Pop Up that displays keyboard shortcuts"""

    IGNORED_DESCRIPTIONS: ClassVar[list[str]] = [
        "Cursor",
        "Focus",
        "Scroll",
        "Page",
    ]
    IGNORED_KEYS: ClassVar[list[str]] = [
        "ctrl+c",
        "super+c",
        "ctrl+q",
        "ctrl+p",
        "shift+space",
        "enter",
        "space",
    ]

    def compose(self) -> ComposeResult:
        """Compose the Shortcuts Pop Up"""
        yield Static("Keyboard Shortcuts", id="shortcuts-header")
        yield DataTable(id="shortcuts-table")
        yield Button("Close", variant="primary", id="close-shortcuts")

    def on_mount(self) -> None:
        """Called when the widget is mounted"""
        table = self.query_one(DataTable)
        table.add_columns("Key", "Description")
        table.cursor_type = "row"
        self.update_shortcuts()

    def _should_ignore_binding(self, binding: BindingType) -> bool:
        """Check if a binding should be ignored"""
        description = binding.description
        key = binding.key
        return any(
            description.startswith(ignored) for ignored in self.IGNORED_DESCRIPTIONS
        ) or any(key == ignored for ignored in self.IGNORED_KEYS)

    def update_shortcuts(self) -> None:
        """Update the shortcuts displayed in the table"""
        table = self.query_one(DataTable)
        table.clear()
        rows = []
        for binding in self.app.active_bindings.values():
            if self._should_ignore_binding(binding.binding):
                continue
            cells = [
                binding.binding.key_display or binding.binding.key,
                binding.binding.description,
            ]
            rows.append(cells)
        sorted_rows = sorted(rows, key=lambda x: x[1])
        for row in sorted_rows:
            table.add_row(*row)

    @on(Button.Pressed, "#close-shortcuts")
    def handle_close(self) -> None:
        """Handle the close button pressed"""
        self.action_close()


class ShortcutsWindow(BaseOverlay):
    """Window containing the Shortcuts Pop Up"""

    BINDINGS: ClassVar[list[BindingType]] = []

    def compose(self) -> ComposeResult:
        """Compose the Shortcuts Window"""
        yield ShortcutsPopUp()
