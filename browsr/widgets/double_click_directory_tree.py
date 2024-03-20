"""
Directory Tree that copeis the path to the clipboard on double click
"""

from __future__ import annotations

import datetime
from typing import Any, ClassVar

from textual import on
from textual.message import Message
from textual.widgets import DirectoryTree
from textual_universal_directorytree import UPath


class DoubleClickDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    _double_click_time: ClassVar[datetime.timedelta] = datetime.timedelta(
        seconds=0.333333
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the DirectoryTree
        """
        super().__init__(*args, **kwargs)
        self._last_clicked_path: UPath = UPath(
            "13041530b3174c569e1895fdfc2676fc57af1e02606059e0d2472d04c1bb360f"
        )
        self._last_clicked_time = datetime.datetime(
            1970, 1, 1, tzinfo=datetime.timezone.utc
        )

    class DoubleClicked(Message):
        """
        A message that is emitted when the directory is changed
        """

        def __init__(self, path: UPath) -> None:
            """
            Initialize the message
            """
            self.path = path
            super().__init__()

    class DirectoryDoubleClicked(DoubleClicked):
        """
        A message that is emitted when the directory is double clicked
        """

    class FileDoubleClicked(DoubleClicked):
        """
        A message that is emitted when the file is double clicked
        """

    @on(DirectoryTree.DirectorySelected)
    def handle_double_click_dir(self, message: DirectoryTree.DirectorySelected) -> None:
        """
        Handle double clicking on a directory
        """
        if (
            self.is_double_click(path=message.path)
            and message.path != self.root.data.path
        ):
            message.stop()
            self.post_message(self.DirectoryDoubleClicked(path=message.path))

    @on(DirectoryTree.FileSelected)
    def handle_double_click_file(self, message: DirectoryTree.FileSelected) -> None:
        """
        Handle double clicking on a file
        """
        if self.is_double_click(path=message.path):
            message.stop()
            self.post_message(self.FileDoubleClicked(path=message.path))

    def is_double_click(self, path: UPath) -> bool:
        """
        Check if the path is double clicked
        """
        click_time = datetime.datetime.now(datetime.timezone.utc)
        click_delta = click_time - self._last_clicked_time
        self._last_clicked_time = click_time
        if self._last_clicked_path == path and click_delta <= self._double_click_time:
            return True
        elif self._last_clicked_path == path and click_delta > self._double_click_time:
            return False
        else:
            self._last_clicked_path = path
            return False
