"""
Extension Classes
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import Any, ClassVar

from textual.app import App
from textual.binding import Binding
from textual.dom import DOMNode
from textual_universal_directorytree import UPath

from browsr.utils import handle_github_url


@dataclass
class TextualAppContext:
    """
    App Context Object
    """

    file_path: str = field(default_factory=os.getcwd)
    config: dict[str, Any] | None = None
    debug: bool = False
    max_file_size: int = 20
    max_lines: int = 1000
    kwargs: dict[str, Any] | None = None

    @property
    def path(self) -> UPath:
        """
        Resolve `file_path` to a UPath object
        """
        if "github" in str(self.file_path).lower():
            file_path = str(self.file_path)
            file_path = file_path.lstrip("https://")  # noqa: B005
            file_path = file_path.lstrip("http://")  # noqa: B005
            file_path = file_path.lstrip("www.")  # noqa: B005
            if file_path.endswith(".git"):
                file_path = file_path[:-4]
            file_path = handle_github_url(url=str(file_path))
            self.file_path = file_path
        if str(self.file_path).endswith("/") and len(str(self.file_path)) > 1:
            self.file_path = str(self.file_path)[:-1]
        storage_options = self.kwargs or {}
        if not self.file_path:
            return pathlib.Path.cwd().resolve()
        else:
            path = UPath(self.file_path, **storage_options)
            return path.resolve()


class SortedBindingsApp(App[str]):
    """
    Textual App with Sorted Bindings
    """

    BINDING_WEIGHTS: ClassVar[dict[str, int]] = {}

    @property
    def namespace_bindings(self) -> dict[str, tuple[DOMNode, Binding]]:
        """
        Return the namespace bindings, optionally sorted by weight

        Bindings are currently returned as they're rendered in the
        current namespace (screen). This method can be overridden to
        return bindings in a specific order.

        Rules:
        - Binding weights must be greater than 0 and less than 10000
        - If a binding is not in the BINDING_WEIGHTS dict, it will be
          given a weight of 500 + its current position in the namespace.
        - Specified weights cannot overlap with the default weights (stay
          away from the 500 range)

        Raises
        ------
        ValueError
            If binding weights are invalid

        Returns
        -------
        dict[str, tuple[DOMNode, Binding]]
            A dictionary of bindings
        """
        existing_bindings = super().namespace_bindings
        if not self.BINDING_WEIGHTS:
            return existing_bindings
        builtin_index = 500
        max_weight = 999
        binding_range = range(builtin_index, builtin_index + len(existing_bindings))
        weights = dict(zip(existing_bindings.keys(), binding_range))
        if max(*self.BINDING_WEIGHTS.values(), 0) > max_weight:
            raise ValueError("Binding weights must be less than 1000")
        elif min(*self.BINDING_WEIGHTS.values(), 1) < 1:
            raise ValueError("Binding weights must be greater than 0")
        elif set(self.BINDING_WEIGHTS.values()).intersection(binding_range):
            raise ValueError("Binding weights must not overlap with existing bindings")
        weights.update(self.BINDING_WEIGHTS)
        updated_bindings = dict(
            sorted(
                existing_bindings.items(),
                key=lambda item: weights[item[0]],
            ),
        )
        return updated_bindings
