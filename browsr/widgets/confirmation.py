from textwrap import dedent
from typing import ClassVar

from rich.markdown import Markdown
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.message import Message
from textual.widgets import Button, Static


class ConfirmationPopUp(Container):
    """
    A Pop Up that asks for confirmation
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    def action_close(self) -> None:
        """
        Close the Confirmation Pop Up
        """
        self.post_message(self.ConfirmationWindowDisplay(display=False))

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

    class ConfirmationWindowDisplay(Message):
        """
        Confirmation Window
        """

        def __init__(self, display: bool) -> None:
            self.display = display
            super().__init__()

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
        self.post_message(self.ConfirmationWindowDisplay(display=False))
        if message.button.variant == "success":
            self.post_message(self.ConfirmationWindowDownload())
        self.post_message(self.DisplayToggle())


class ConfirmationWindow(Container):
    """
    Window containing the Confirmation Pop Up
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    def action_close(self) -> None:
        """
        Close the Confirmation Pop Up
        """
        self.display = False

    @on(ConfirmationPopUp.ConfirmationWindowDisplay)
    def handle_confirmation_window_display(
        self, message: ConfirmationPopUp.ConfirmationWindowDisplay
    ) -> None:
        """
        Handle Confirmation Window Display
        """
        self.display = message.display
