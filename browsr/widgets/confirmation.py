"""
Confirmation Widget
"""

from __future__ import annotations

from textwrap import dedent

from rich.markdown import Markdown
from textual import on
from textual.app import ComposeResult
from textual.events import Key
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

    def action_close(self) -> None:
        """
        Close the popup and restore the previous display state.
        """
        super().action_close()
        self.post_message(self.DisplayToggle())

    def compose(self) -> ComposeResult:
        """
        Compose the Confirmation Pop Up
        """
        self.download_message = Static(Markdown(""))
        yield self.download_message
        yield Button("Yes (y)", variant="success", id="confirm-yes")
        yield Button("No (n)", variant="error", id="confirm-no")

    def prompt_download(self, file_path: str, download_path: str) -> None:
        """
        Prompt the user to download a file
        """
        prompt_message: str = dedent(
            f"""
            ## File Download

            **Are you sure you want to download that file?**

            **File:** `{file_path}`

            **Path:** `{download_path}`
            """
        )
        self.download_message.update(Markdown(prompt_message))
        self.refresh()

    @on(Button.Pressed)
    def handle_download_selection(self, message: Button.Pressed) -> None:
        """
        Handle Button Presses
        """
        self.action_close()
        if message.button.variant == "success":
            self.post_message(self.ConfirmationWindowDownload())

    @on(Key)
    def handle_key_press(self, message: Key) -> None:
        """
        Handle Key Presses
        """
        if message.key.lower() == "y":
            self.post_message(self.ConfirmationWindowDownload())
            self.action_close()
        elif message.key.lower() == "n":
            self.action_close()


class ConfirmationWindow(BaseOverlay):
    """
    Window containing the Confirmation Pop Up
    """

    def action_close(self) -> None:
        """
        Close the overlay and restore the previous display state.
        """
        super().action_close()
        self.post_message(ConfirmationPopUp.DisplayToggle())
