"""
A universal directory tree widget for Textual.
"""

from __future__ import annotations

from typing import ClassVar, Iterable

from textual.binding import Binding, BindingType
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode
from textual_universal_directorytree import UniversalDirectoryTree, UPath

from browsr.widgets.double_click_directory_tree import DoubleClickDirectoryTree
from browsr.widgets.keys import vim_cursor_bindings, keypad_cursor_bindings


class BrowsrDirectoryTree(DoubleClickDirectoryTree, UniversalDirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        *UniversalDirectoryTree.BINDINGS,
        *vim_cursor_bindings,
        *keypad_cursor_bindings,
        Binding(key="h,left,kp_left", action="collapse_parent", description="Collapse (Parent) Directory", show=False),
        Binding(key="l,right,kp_right", action="expand_or_select", description="Expand Directory or Select File", show=False),
    ]

    @classmethod
    def _handle_top_level_bucket(cls, dir_path: UPath) -> Iterable[UPath] | None:
        """
        Handle scenarios when someone wants to browse all of s3

        This is because S3FS handles the root directory differently
        than other filesystems
        """
        if str(dir_path) == "s3:/":
            sub_buckets = sorted(
                UPath(f"s3://{bucket.name}") for bucket in dir_path.iterdir()
            )
            return sub_buckets
        return None

    def _populate_node(
        self, node: TreeNode[DirEntry], content: Iterable[UPath]
    ) -> None:
        """
        Populate the given tree node with the given directory content.

        This function overrides the original textual method to handle root level
        cloud buckets.
        """
        top_level_buckets = self._handle_top_level_bucket(dir_path=node.data.path)
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

    def action_collapse_parent(self) -> None:
        cursor_node = self.cursor_node
        cursor_path = cursor_node.data.path
        collapse_parent = False
        if self._safe_is_dir(cursor_path):
            if cursor_node.is_expanded:
                cursor_node.collapse()
            elif not cursor_node.is_root:
                collapse_parent = True
        else:
            collapse_parent = True
        if collapse_parent:
            self.action_cursor_parent()
            cursor_node.parent.collapse()

    def action_expand_or_select(self) -> None:
        cursor_node = self.cursor_node
        cursor_path = cursor_node.data.path
        if self._safe_is_dir(cursor_path):
            if not cursor_node.is_expanded:
                cursor_node.expand()
        else:
            self.action_select_cursor()
