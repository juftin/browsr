from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.message import Message
from textual.widgets import Button, DataTable, Static


class ShortcutsPopUp(Container):
    """A Pop Up that displays keyboard shortcuts"""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "toggle", "Close", show=False),
        Binding("q", "toggle", "Close", show=False),
    ]

    class Toggle(Message):
        """Toggle the Shortcuts Window"""

    def action_toggle(self) -> None:
        """Toggle the Shortcuts Window"""
        self.post_message(self.Toggle())

    def compose(self) -> ComposeResult:

        yield Static("Keyboard Shortcuts", id="shortcuts-header")
        yield DataTable(id="shortcuts-table")
        yield Button("Close", variant="primary", id="close-shortcuts")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Key", "Description")
        table.cursor_type = "row"
        self.update_shortcuts()

    def update_shortcuts(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        ignored_bindings = [
            "Cursor",
            "Focus",
            "Scroll",
            "Page",
        ]
        ignored_keys = [
            "ctrl+c",
            "super+c",
            "ctrl+q",
            "ctrl+p",
            "shift+space",
            "enter",
            "space",
        ]
        rows = []
        for binding in self.app.active_bindings.values():
            if any(
                binding.binding.description.startswith(ignored)
                for ignored in ignored_bindings
            ) or any(binding.binding.key == ignored for ignored in ignored_keys):
                continue
            else:
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
        self.post_message(self.Toggle())


class ShortcutsWindow(Container):
    """Window containing the Shortcuts Pop Up"""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "toggle", "Close", show=False),
        Binding("q", "toggle", "Close", show=False),
    ]

    def action_toggle(self) -> None:
        """Toggle the Shortcuts Window"""
        self.display = False

    def compose(self) -> ComposeResult:
        """Compose the Shortcuts Window"""
        yield ShortcutsPopUp()

    @on(ShortcutsPopUp.Toggle)
    def handle_toggle(self) -> None:
        self.display = False
