"""
A universal directory tree widget for Textual.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Iterable, Optional

import upath
from textual.events import Mount
from textual.reactive import var
from textual.widgets import DirectoryTree
from textual.widgets._tree import Tree, TreeNode
from upath import UPath as Path

upath.registry._registry.known_implementations[
    "github"
] = "browsr.universal_directory_tree.GitHubPath"


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

    This class is copied almost completely from the `DirectoryTree` widget in
    Textual. The only difference is that it uses `upath.Path` instead of
    `pathlib.Path`. Due to the way that `pathlib.Path` is implemented on the
    `DirectoryTree` widget (such as the __init__ method), it is not possible to
    simply subclass it. Instead, the code has been copied to recreate the widget
    with the necessary changes:

    - `from upath import UPath as Path`
    - CSS Change: DirectoryTree > UniversalDirectoryTree
    - `_on_mount` -> This function has been modified to prevent duplicate loading
    - `_load_directory` -> This function has been modified to use `upath.Path`
    - `validate_path` -> This function has been modified to use `upath.Path`
    - `reload` -> This function has been modified to use `upath.Path`
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = DirectoryTree.COMPONENT_CLASSES
    DEFAULT_CSS = DirectoryTree.DEFAULT_CSS.replace(
        "DirectoryTree", "UniversalDirectoryTree"
    )
    watch_path = DirectoryTree.watch_path
    process_label = DirectoryTree.process_label  # type: ignore[assignment]
    render_label = DirectoryTree.render_label  # type: ignore[assignment]
    filter_paths = DirectoryTree.filter_paths
    _on_tree_node_expanded = DirectoryTree._on_tree_node_expanded
    _on_tree_node_selected = DirectoryTree._on_tree_node_selected

    class FileSelected(DirectoryTree.FileSelected):
        """
        Posted when a file is selected.
        """

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

    def _on_mount(self, _: Mount) -> None:
        """
        Perform actions on widget mount.

        This function overrides the original textual method to prevent duplicate loading.
        """
        pass

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
                self.filter_paths(node.data.path.iterdir()),  # type: ignore[misc]
                key=lambda path: (not path.is_dir(), path.name.lower()),
            )
        for path in top_level_buckets or directory:
            if top_level_buckets is None:
                path_name = path.name
            else:
                path_name = str(path).replace("s3://", "").rstrip("/")
            node.add(
                path_name,
                data=DirEntry(path),  # type: ignore[arg-type]
                allow_expand=path.is_dir(),
            )
        node.expand()


class GitHubPath(upath.core.UPath):
    """
    GitHubPath

    UPath implementation for GitHub to be compatible with
    the Universal Directory Tree
    """

    @property
    def path(self) -> str:
        """
        Paths get their leading slash stripped
        """
        return super().path.strip("/")

    @property
    def name(self) -> str:
        """
        Override the name for top level repo
        """
        if self.path == "":
            org = self._accessor._fs.org
            repo = self._accessor._fs.repo
            sha = self._accessor._fs.sha
            github_name = f"{org}:{repo}@{sha}"
            return github_name
        else:
            return super().name

    def __getattr__(self, item: str) -> Any:
        """
        Override the getattr method to allow for the name attribute override

        This is necessary because the name attribute is not a property
        of the UPath class
        """
        if item == "name":
            github_name = (
                f"{self._accessor._fs.org}:"
                f"{self._accessor._fs.repo}"
                f"@{self._accessor._fs.storage_options['sha']}"
            )
            return github_name
        else:
            return super().__getattr__(item)
