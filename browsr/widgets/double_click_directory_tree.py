"""
Directory Tree that copeis the path to the clipboard on double click
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from textual import on
from textual.message import Message
from textual.widgets import DirectoryTree
from textual_universal_directorytree import UPath


class DoubleClickDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the DirectoryTree
        """
        super().__init__(*args, **kwargs)
        self._last_clicked_path: os.PathLike[UPath] = UPath(uuid.uuid4().hex)

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

    def is_double_click(self, path: os.PathLike[Any]) -> bool:
        """
        Check if the path is double clicked
        """
        if self._last_clicked_path != path:
            self._last_clicked_path = path
            return False
        else:
            return True
