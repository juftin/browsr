from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widgets import Button, DataTable, Static


class ShortcutsPopUp(Container):
    """A Pop Up that displays keyboard shortcuts"""

    class Toggle(Message):
        """Toggle the Shortcuts Window"""

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
        # Use active_bindings to get deduplicated and prioritized shortcuts
        for binding in self.app.active_bindings:
            if binding.show:
                table.add_row(binding.key, binding.description)

    @on(Button.Pressed, "#close-shortcuts")
    def handle_close(self) -> None:
        self.post_message(self.Toggle())


class ShortcutsWindow(Container):
    """Window containing the Shortcuts Pop Up"""

    @on(ShortcutsPopUp.Toggle)
    def handle_toggle(self) -> None:
        self.display = False
