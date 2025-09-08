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
keypad_scroll_bindings = [
    Binding(key="kp_up", action="scroll_up", description="Scroll Up", show=False),
    Binding(key="kp_down", action="scroll_down", description="Scroll Down", show=False),
    Binding(key="kp_left", action="scroll_left", description="Scroll Left", show=False),
    Binding(key="kp_right", action="scroll_right", description="Scroll Right", show=False),
    Binding(key="kp_page_up", action="page_up", description="Page Up", show=False),
    Binding(key="kp_page_down", action="page_down", description="Page Down", show=False),
    Binding(key="kp_home", action="scroll_home", description="Scroll Home", show=False),
    Binding(key="kp_end", action="scroll_end", description="Scroll End", show=False),
]
keypad_cursor_bindings = [
    Binding(key="kp_up", action="cursor_up", description="Cursor Up", show=False),
    Binding(key="kp_down", action="cursor_down", description="Cursor Down", show=False),
    Binding(key="kp_left", action="cursor_left", description="Cursor Left", show=False),
    Binding(key="kp_right", action="cursor_right", description="Cursor Right", show=False),
    Binding(key="kp_page_up", action="page_up", description="Page Up", show=False),
    Binding(key="kp_page_down", action="page_down", description="Page Down", show=False),
    Binding(key="kp_home", action="scroll_home", description="Scroll Home", show=False),
    Binding(key="kp_end", action="scroll_end", description="Scroll End", show=False),
    Binding(key="kp_enter", action="select_cursor", description="Select Item", show=False),
]


class KeyBindScroll(VerticalScroll):
    """
    A VerticalScroll with Vim and Keypad Keybindings
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        *VerticalScroll.BINDINGS,
        *vim_scroll_bindings,
        *keypad_scroll_bindings,
    ]


class KeyBindDataTable(DataTable[str]):
    """
    A DataTable with Vim and Keypad Keybindings
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        *DataTable.BINDINGS,
        *vim_cursor_bindings,
        *keypad_cursor_bindings,
    ]
