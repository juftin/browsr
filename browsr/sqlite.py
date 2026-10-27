"""Read-only access to local and remote SQLite databases."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, NamedTuple

from textual_universal_directorytree import UPath, is_remote_path


class SQLiteObject(NamedTuple):
    """A user table or view available for browsing."""

    name: str
    kind: str


class SQLitePage(NamedTuple):
    """A bounded page of results, including empty-table column names."""

    columns: list[str]
    rows: list[tuple[Any, ...]]
    has_next: bool


class SQLiteDatabase:
    """Keep a database read-only and clean up downloaded copies on close."""

    def __init__(self, file_path: UPath) -> None:
        self.connection: sqlite3.Connection | None = None
        self._temporary_directory: TemporaryDirectory[str] | None = None
        self.objects: list[SQLiteObject] = []
        self._object_names: set[str] = set()
        try:
            if is_remote_path(file_path):
                self._temporary_directory = TemporaryDirectory(prefix="browsr-sqlite-")
                local_path = Path(self._temporary_directory.name) / "database.sqlite"
                with file_path.open("rb") as source, local_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
            else:
                local_path = Path(file_path).resolve()
            self.connection = sqlite3.connect(
                f"{local_path.as_uri()}?mode=ro", uri=True, timeout=1
            )
            self.connection.execute("PRAGMA query_only = ON")
            self.objects = [
                SQLiteObject(name, kind)
                for name, kind in self.connection.execute(
                    "SELECT name, type FROM sqlite_master "
                    "WHERE type IN ('table', 'view') AND name NOT GLOB 'sqlite_*' "
                    "ORDER BY name"
                )
            ]
            self._object_names = {item.name for item in self.objects}
        except Exception:
            self.close()
            raise

    def read_page(self, name: str, offset: int, limit: int) -> SQLitePage:
        """Read at most one page and one lookahead row without counting all rows."""
        if self.connection is None:
            raise ValueError("The database is closed")
        if name not in self._object_names:
            raise ValueError("Unknown table or view")
        if limit < 1 or offset < 0:
            raise ValueError("Page size must be positive and offset cannot be negative")
        # SQLite identifiers cannot be bound as parameters; quote embedded quotes.
        identifier = '"' + name.replace('"', '""') + '"'
        cursor = self.connection.execute(
            f"SELECT * FROM {identifier} LIMIT ? OFFSET ?",  # noqa: S608
            (limit + 1, offset),
        )
        try:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return SQLitePage(columns, rows[:limit], len(rows) > limit)

    def close(self) -> None:
        """Release the connection before deleting any downloaded database."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None
        self._object_names.clear()
