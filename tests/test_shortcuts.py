from typing import ClassVar

import pytest
from textual.app import App
from textual.binding import Binding

from browsr.widgets.shortcuts import ShortcutsPopUp


class MockApp(App):
    BINDINGS: ClassVar[list[Binding]] = [Binding("q", "quit", "Quit")]


@pytest.mark.asyncio
async def test_shortcut_discovery():
    app = MockApp()
    async with app.run_test():
        popup = ShortcutsPopUp()
        await app.mount(popup)
        # Note: the widget calls update_shortcuts on mount
        table = popup.query_one("#shortcuts-table")
        assert table.row_count > 0
