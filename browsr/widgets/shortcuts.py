"""
Shortcuts Widget
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable, Static

from browsr.widgets.base import BaseOverlay, BasePopUp


class ShortcutsPopUp(BasePopUp):
    """A Pop Up that displays keyboard shortcuts"""

    class DisplayToggle(Message):
        """Shortcuts window display"""

    TRUSTED_ACTIONS: ClassVar[list[str]] = [
        "copy_file_path",
        "copy_text",
        "download_file",
        "toggle_files",
        "parent_dir",
        "quit",
        "reload",
        "toggle_shortcuts",
        "toggle_dark",
        "linenos",
        "theme",
        "toggle_wrap",
    ]
    DESCRIPTION_MAPPINGS: ClassVar[dict[str, str]] = {
        "toggle_dark": "Toggle Dark Mode",
        "linenos": "Toggle Line Numbers",
        "theme": "Toggle Theme",
        "download_file": "Download File",
        "toggle_shortcuts": "Show/Hide Shortcuts",
    }

    IGNORED_KEYS: ClassVar[list[str]] = ["ctrl+q"]

    def compose(self) -> ComposeResult:
        """Compose the Shortcuts Pop Up"""
        yield Static("Keyboard Shortcuts", id="shortcuts-header")
        yield DataTable(id="shortcuts-table", show_cursor=False, zebra_stripes=True)

    def action_close(self) -> None:
        """Close the popup and restore the previous display state."""
        super().action_close()
        self.post_message(self.DisplayToggle())

    def on_mount(self) -> None:
        """Called when the widget is mounted"""
        table = self.query_one(DataTable)
        table.add_columns("Key", "Description")
        table.cursor_type = "row"
        self.update_shortcuts()

    def update_shortcuts(self) -> None:
        """Update the shortcuts displayed in the table"""
        table = self.query_one(DataTable)
        table.clear()
        rows = []
        for active_binding in self.app.active_bindings.values():
            binding = active_binding.binding
            if not isinstance(binding, Binding):
                continue
            key = binding.key_display or binding.key
            if binding.action not in self.TRUSTED_ACTIONS or key in self.IGNORED_KEYS:
                continue
            description = self.DESCRIPTION_MAPPINGS.get(
                binding.action, binding.description
            )
            cells = [key, description]
            rows.append(cells)
        sorted_rows = sorted(rows, key=lambda x: x[1])
        for row in sorted_rows:
            table.add_row(*row)


class ShortcutsWindow(BaseOverlay):
    """Window containing the Shortcuts Pop Up"""

    def action_close(self) -> None:
        """Close the overlay and restore the previous display state."""
        super().action_close()
        self.post_message(ShortcutsPopUp.DisplayToggle())
