from __future__ import annotations

import math

from rich.console import RenderableType
from rich.text import Text
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget

from browsr.utils import FileInfo


class CurrentFileInfoBar(Widget):
    """
    A Widget that displays information about the currently selected file

    Thanks, Kupo. https://github.com/darrenburns/kupo
    """

    file_info: FileInfo | None = reactive(None)

    class FileInfoUpdate(Message):
        """
        File Info Bar Update
        """

        def __init__(self, new_file: FileInfo | None) -> None:
            self.new_file = new_file
            super().__init__()

    def watch_file_info(self, new_file: FileInfo | None) -> None:
        """
        Watch the file_info property for changes
        """
        if new_file is None:
            self.display = False
        else:
            self.display = True

    @classmethod
    def _convert_size(cls, size_bytes: int) -> str:
        """
        Convert Bytes to Human Readable String
        """
        if size_bytes == 0:
            return " 0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        index = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, index)
        number = round(size_bytes / p, 2)
        unit = size_name[index]
        return f"{number:.0f}{unit}"

    def render(self) -> RenderableType:
        """
        Render the Current File Info Bar
        """
        if self.file_info is None or not self.file_info.is_file:
            return Text("")
        status_string = "🗄️️️  " + self._convert_size(self.file_info.size)
        if (
            self.file_info.last_modified is not None
            and self.file_info.last_modified.timestamp() != 0
        ):
            modify_time = self.file_info.last_modified.strftime("%b %d, %Y %I:%M %p")
            status_string += "  📅  " + modify_time
        parent_name = self.file_info.file.parent.name
        if not parent_name:
            parent_name = str(self.file_info.file.parent)
            parent_name = parent_name.lstrip(f"{self.file_info.file.protocol}://")
            parent_name = parent_name.rstrip("/")
        status_string += "  💾  " + self.file_info.file.name + "  📂  " + parent_name
        if self.file_info.owner not in ["", None]:
            status_string += "  👤  " + self.file_info.owner
        if self.file_info.group.strip() not in ["", None]:
            status_string += "  🏠  " + self.file_info.group
        return Text(status_string, style="dim")
