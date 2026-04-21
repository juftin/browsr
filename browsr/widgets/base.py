"""
Base classes for widgets
"""

from __future__ import annotations

from typing import ClassVar

from textual import on
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.message import Message


class BasePopUp(Container):
    """
    Base class for popup widgets
    """

    can_focus = True

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    class Toggle(Message):
        """
        Toggle the popup visibility
        """

        def __init__(self, display: bool | None = None) -> None:
            self.display = display
            super().__init__()

    def action_close(self) -> None:
        """
        Close the popup
        """
        self.post_message(self.Toggle(display=False))


class BaseOverlay(Container):
    """
    Base class for overlay containers
    """

    can_focus = True

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    def action_close(self) -> None:
        """
        Close the overlay
        """
        self.display = False

    def on_mount(self) -> None:
        """
        On Mount
        """
        self.display = False

    def watch_display(self, display: bool) -> None:
        """
        Focus the overlay when it is displayed
        """
        if display:
            self.focus()

    @on(BasePopUp.Toggle)
    def handle_toggle(self, message: BasePopUp.Toggle) -> None:
        """
        Handle the toggle message from the popup
        """
        if message.display is False:
            self.action_close()
        elif message.display is True:
            self.display = True
        elif self.display:
            self.action_close()
        else:
            self.display = True
