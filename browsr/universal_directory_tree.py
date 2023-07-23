"""
A universal directory tree widget for Textual.
"""

from __future__ import annotations

from typing import Iterable, Optional

from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode
from textual_universal_directorytree import UniversalDirectoryTree
from upath import UPath as Path

from browsr._base import vim_cursor_bindings


class BrowsrDirectoryTree(UniversalDirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    BINDINGS = [
        *UniversalDirectoryTree.BINDINGS,
        *vim_cursor_bindings,
    ]

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

    def _populate_node(self, node: TreeNode[DirEntry], content: Iterable[Path]) -> None:  # type: ignore[override]
        """
        Populate the given tree node with the given directory content.

        This function overrides the original textual method to handle root level
        cloud buckets.
        """
        top_level_buckets = self._handle_top_level_bucket(dir_path=node.data.path)  # type: ignore[union-attr, arg-type]
        if top_level_buckets is not None:
            content = top_level_buckets
        node.remove_children()
        for path in content:
            if top_level_buckets is not None:
                path_name = str(path).replace("s3://", "").rstrip("/")
            else:
                path_name = path.name
            node.add(
                path_name,
                data=DirEntry(path),
                allow_expand=self._safe_is_dir(path),
            )
        node.expand()
