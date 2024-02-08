from __future__ import annotations

from typing import ClassVar

from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.widgets import DataTable

vim_scroll_bindings = [
    Binding(key="k", action="scroll_up", description="Scroll Up", show=False),
    Binding(key="j", action="scroll_down", description="Scroll Down", show=False),
    Binding(key="h", action="scroll_left", description="Scroll Left", show=False),
    Binding(key="l", action="scroll_right", description="Scroll Right", show=False),
]
vim_cursor_bindings = [
    Binding(key="k", action="cursor_up", description="Cursor Up", show=False),
    Binding(key="j", action="cursor_down", description="Cursor Down", show=False),
    Binding(key="h", action="cursor_left", description="Cursor Left", show=False),
    Binding(key="l", action="cursor_right", description="Cursor Right", show=False),
]


class VimScroll(VerticalScroll):
    """
    A VerticalScroll with Vim Keybindings
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        *VerticalScroll.BINDINGS,
        *vim_scroll_bindings,
    ]


class VimDataTable(DataTable[str]):
    """
    A DataTable with Vim Keybindings
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        *DataTable.BINDINGS,
        *vim_cursor_bindings,
    ]
