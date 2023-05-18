"""
A universal directory tree widget for Textual.
"""

from __future__ import annotations

from os import getenv
from typing import Iterable, Optional

import textual
import upath
from textual.widgets import DirectoryTree
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode
from upath import UPath as Path

upath.registry._registry.known_implementations[
    "github"
] = "browsr.universal_directory_tree.GitHubPath"

# This is the secret sauce behind the UniversalDirectoryTree
# It allows us to use the upath.Path as the Path implementation in the
# underlying DirectoryTree widget
textual.widgets._directory_tree.Path = Path  # type: ignore[attr-defined]


class UniversalDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that can handle any filesystem.
    """

    DEFAULT_CSS = DirectoryTree.DEFAULT_CSS.replace(
        "DirectoryTree", "UniversalDirectoryTree"
    )

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


class GitHubPath(upath.core.UPath):
    """
    GitHubPath

    UPath implementation for GitHub to be compatible with
    the Universal Directory Tree
    """

    def __new__(cls, *args, **kwargs) -> "GitHubPath":  # type: ignore[no-untyped-def]
        """
        Attempt to set the username and token from the environment
        """
        token = getenv("GITHUB_TOKEN")
        if token is not None:
            kwargs.update({"username": "Bearer", "token": token})
        github_path = super().__new__(cls, *args, **kwargs)
        return github_path

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
            sha = self._accessor._fs.storage_options["sha"]
            github_name = f"{org}:{repo}@{sha}"
            return github_name
        else:
            return super().name
