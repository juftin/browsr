"""
A universal directory tree widget for Textual.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Iterable, Optional

from rich.style import Style
from rich.text import Text, TextType
from textual.events import Mount
from textual.message import Message
from textual.reactive import var
from textual.widgets._tree import TOGGLE_STYLE, Tree, TreeNode
from upath import UPath as Path


@dataclass
class DirEntry:
    """
    Attaches directory information to a node.
    """

    path: Path
    loaded: bool = False


class UniversalDirectoryTree(Tree[DirEntry]):
    """
    A Tree widget that presents files and directories.

    This class is copied almost verbatim from the `DirectoryTree` widget in
    Textual. The only difference is that it uses `upath.Path` instead of
    `pathlib.Path`. The support this the following code changes have been made:

    - from upath import UPath as Path
    - CSS Change: DirectoryTree > UniversalDirectoryTree
    - `_on_mount` -> This function has been disabled to prevent duplicate loading
    - `_load_directory` -> This function has been modified to use `upath.Path`
    - docstrings have been trimmed and updated to reflect the changes
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "directory-tree--extension",
        "directory-tree--file",
        "directory-tree--folder",
        "directory-tree--hidden",
    }

    DEFAULT_CSS = """
    UniversalDirectoryTree > .directory-tree--folder {
        text-style: bold;
    }

    UniversalDirectoryTree > .directory-tree--extension {
        text-style: italic;
    }

    UniversalDirectoryTree > .directory-tree--hidden {
        color: $text 50%;
    }
    """

    class FileSelected(Message, bubble=True):
        """
        Posted when a file is selected.

        Can be handled using `on_directory_tree_file_selected` in a subclass of
        `UniversalDirectoryTree` or in a parent widget in the DOM.
        """

        def __init__(
            self, tree: UniversalDirectoryTree, node: TreeNode[DirEntry], path: Path
        ) -> None:
            """
            Initialise the FileSelected object.
            """
            super().__init__()
            self.tree: UniversalDirectoryTree = tree
            self.node: TreeNode[DirEntry] = node
            self.path: Path = path

        @property
        def control(self) -> UniversalDirectoryTree:  # type: ignore[override]
            """
            The `UniversalDirectoryTree` that had a file selected.
            """
            return self.tree

    path: var[str | Path] = var["str | Path"](Path("."), init=False)

    def __init__(
        self,
        path: str | Path,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """
        Initialise the directory tree.
        """
        super().__init__(
            str(path),
            data=DirEntry(Path(path)),
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.path = path

    def reload(self) -> None:
        """
        Reload the `UniversalDirectoryTree` contents.
        """
        self.reset(str(self.path), DirEntry(Path(self.path)))
        self._load_directory(self.root)

    def validate_path(self, path: str | Path) -> Path:
        """
        Ensure that the path is of the `Path` type.
        """
        return Path(path)

    def watch_path(self) -> None:
        """
        Watch for changes to the `path` of the directory tree.
        """
        self.reload()

    def process_label(self, label: TextType) -> Text:
        """
        Process a str or Text into a label.
        """
        if isinstance(label, str):
            text_label = Text(label)
        else:
            text_label = label
        first_line = text_label.split()[0]
        return first_line

    def render_label(
        self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
        """
        Render a label for the given node.
        """
        node_label = node._label.copy()
        node_label.stylize(style)

        if node._allow_expand:
            prefix = ("📂 " if node.is_expanded else "📁 ", base_style + TOGGLE_STYLE)
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--folder", partial=True)
            )
        else:
            prefix = (
                "📄 ",
                base_style,
            )
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--file", partial=True),
            )
            node_label.highlight_regex(
                r"\..+$",
                self.get_component_rich_style(
                    "directory-tree--extension", partial=True
                ),
            )

        if node_label.plain.startswith("."):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden")
            )

        text = Text.assemble(prefix, node_label)
        return text

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """
        Filter the paths before adding them to the tree.
        """
        return paths

    def _on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:  # type: ignore[type-arg]
        """
        Handle when a node is expanded.
        """
        event.stop()
        dir_entry = event.node.data
        if dir_entry is None:
            return
        if dir_entry.path.is_dir():
            if not dir_entry.loaded:
                self._load_directory(event.node)
        else:
            self.post_message(self.FileSelected(self, event.node, dir_entry.path))

    def _on_tree_node_selected(self, event: Tree.NodeSelected) -> None:  # type: ignore[type-arg]
        """
        Handle when a node is selected.
        """
        event.stop()
        dir_entry = event.node.data
        if dir_entry is None:
            return
        if not dir_entry.path.is_dir():
            self.post_message(self.FileSelected(self, event.node, dir_entry.path))

    @classmethod
    def _handle_top_level_bucket(cls, dir_path: Path) -> Optional[Iterable[Path]]:
        """
        Handle scenarios when someone wants to browse all of s3

        This is because S3FS handles the root directory differently than other filesystems
        """
        if str(dir_path) == "s3:/":
            sub_buckets = sorted(
                Path(f"s3://{bucket.name}") for bucket in dir_path.iterdir()
            )
            return sub_buckets
        return None

    def _on_mount(self, _: Mount) -> None:
        """
        Perform Action on Mount.

        This function overrides the original textual method
        """
        pass

    def _load_directory(self, node: TreeNode[DirEntry]) -> None:
        """
        Load the directory contents for a given node.

        This function overrides the original textual method
        """
        assert node.data is not None
        node.data.loaded = True
        top_level_buckets = self._handle_top_level_bucket(dir_path=node.data.path)
        if top_level_buckets is None:
            directory = sorted(
                self.filter_paths(node.data.path.iterdir()),
                key=lambda path: (not path.is_dir(), path.name.lower()),
            )
        for path in top_level_buckets or directory:
            if top_level_buckets is None:
                path_name = path.name
            else:
                path_name = str(path).replace("s3://", "").rstrip("/")
            node.add(
                path_name,
                data=DirEntry(path),
                allow_expand=path.is_dir(),
            )
        node.expand()
