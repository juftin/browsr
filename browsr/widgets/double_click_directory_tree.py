"""
Directory Tree that copeis the path to the clipboard on double click
"""

from __future__ import annotations

import datetime
import os
import pathlib
import uuid
from typing import Any

from textual import on
from textual.message import Message
from textual.widgets import DirectoryTree


class DoubleClickDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the DirectoryTree
        """
        super().__init__(*args, **kwargs)
        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self._current_path: os.PathLike[Any] = pathlib.Path(uuid.uuid4().hex)
        self._current_path_time: datetime.datetime = (
            current_timestamp - datetime.timedelta(seconds=5)
        )
        self._last_clicked_path: os.PathLike[Any] = pathlib.Path(uuid.uuid4().hex)
        self._last_clicked_path_time: datetime.datetime = (
            current_timestamp - datetime.timedelta(seconds=10)
        )

    class DoubleClicked(Message):
        """
        A message that is emitted when the directory is changed
        """

        def __init__(self, path: os.PathLike[Any]) -> None:
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
        self.handle_click(path=message.path)
        if self.is_double_click():
            message.stop()
            self.post_message(self.DirectoryDoubleClicked(path=message.path))

    @on(DirectoryTree.FileSelected)
    def handle_double_click_file(self, message: DirectoryTree.FileSelected) -> None:
        """
        Handle double clicking on a file
        """
        self.handle_click(path=message.path)
        if self.is_double_click():
            message.stop()
            self.post_message(self.FileDoubleClicked(path=message.path))

    def handle_click(self, path: os.PathLike[Any]) -> None:
        """
        Handle clicking on a directory
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        self._last_clicked_path = self._current_path
        self._last_clicked_path_time = self._current_path_time
        self._current_path = path
        self._current_path_time = now

    def is_double_click(self) -> bool:
        """
        Check if the path is double clicked
        """
        return all(
            (
                str(self._last_clicked_path) == str(self._current_path),
                self._last_clicked_path_time
                >= self._current_path_time - datetime.timedelta(seconds=0.5),
            )
        )
