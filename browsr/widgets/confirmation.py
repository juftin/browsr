"""
Confirmation Widget
"""

from __future__ import annotations

from textwrap import dedent

from rich.markdown import Markdown
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, Static

from browsr.widgets.base import BaseOverlay, BasePopUp


class ConfirmationPopUp(BasePopUp):
    """
    A Pop Up that asks for confirmation
    """

    __confirmation_message__: str = dedent(
        """
        ## File Download

        Are you sure you want to download that file?
        """
    )

    class ConfirmationWindowDownload(Message):
        """
        Confirmation Window
        """

    class DisplayToggle(Message):
        """
        TableView Display
        """

    def compose(self) -> ComposeResult:
        """
        Compose the Confirmation Pop Up
        """
        self.download_message = Static(Markdown(""))
        yield self.download_message
        yield Button("Yes", variant="success")
        yield Button("No", variant="error")

    @on(Button.Pressed)
    def handle_download_selection(self, message: Button.Pressed) -> None:
        """
        Handle Button Presses
        """
        self.action_close()
        if message.button.variant == "success":
            self.post_message(self.ConfirmationWindowDownload())
        self.post_message(self.DisplayToggle())


class ConfirmationWindow(BaseOverlay):
    """
    Window containing the Confirmation Pop Up
    """

    def compose(self) -> ComposeResult:
        """
        Compose the Confirmation Window
        """
        yield ConfirmationPopUp()
