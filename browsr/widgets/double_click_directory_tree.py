"""
Directory Tree that copeis the path to the clipboard on double click
"""

import inspect
import os
import pathlib
import uuid
from typing import Any

import pyperclip
from textual import on
from textual.message import Message
from textual.widgets import DirectoryTree
from textual_universal_directorytree import UniversalDirectoryTree


class DoubleClickDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the DirectoryTree
        """
        super().__init__(*args, **kwargs)
        self._copy_function = pyperclip.determine_clipboard()[0]
        self._copy_supported = inspect.isfunction(self._copy_function)
        self._last_clicked_path: os.PathLike[Any] = pathlib.Path(uuid.uuid4().hex)

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

    @on(UniversalDirectoryTree.DirectorySelected)
    def handle_double_click_dir(
        self, message: UniversalDirectoryTree.DirectorySelected
    ) -> None:
        """
        Handle double clicking on a directory
        """
        if self.is_double_click(path=message.path):
            message.stop()
            self.post_message(self.DirectoryDoubleClicked(path=message.path))

    @on(UniversalDirectoryTree.FileSelected)
    def handle_double_click_file(
        self, message: UniversalDirectoryTree.FileSelected
    ) -> None:
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
        if str(self._last_clicked_path) != str(path):
            self._last_clicked_path = path
            return False
        else:
            return True
