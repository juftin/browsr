"""SQLite access and integration with the browser's file previews."""

import sqlite3
from pathlib import Path

import pytest
from textual.widgets import TabbedContent
from textual_universal_directorytree import UPath

from browsr.base import TextualAppContext
from browsr.browsr import Browsr
from browsr.sqlite import SQLiteDatabase


@pytest.fixture
def database_path(tmp_path: Path) -> UPath:
    path = tmp_path / "example #1.sqlite"
    connection = sqlite3.connect(path)
    with connection:
        connection.execute(
            'CREATE TABLE "a weird "" table" (id INTEGER, value, data BLOB)'
        )
        connection.executemany(
            'INSERT INTO "a weird "" table" VALUES (?, ?, ?)',
            [(1, "[bold]literal[/bold]", b"\x00\xff"), (2, None, b""), (3, 1.5, None)],
        )
        connection.execute("CREATE TABLE empty (name TEXT)")
        connection.execute(
            'CREATE VIEW example_view AS SELECT * FROM "a weird "" table"'
        )
        connection.execute("CREATE VIEW broken_view AS SELECT * FROM missing_table")
    connection.close()
    return UPath(path)


def test_read_only_paging_and_quoted_identifiers(database_path: UPath) -> None:
    database = SQLiteDatabase(database_path)
    try:
        assert [item.name for item in database.objects] == [
            'a weird " table',
            "broken_view",
            "empty",
            "example_view",
        ]
        page = database.read_page('a weird " table', offset=0, limit=2)
        assert page.columns == ["id", "value", "data"]
        assert page.rows == [(1, "[bold]literal[/bold]", b"\x00\xff"), (2, None, b"")]
        assert page.has_next is True
        assert database.read_page('a weird " table', 2, 2).rows == [(3, 1.5, None)]
        assert database.read_page('a weird " table', 2, 2).has_next is False
        assert database.read_page("example_view", 0, 2) == page
        assert database.read_page("empty", 0, 2).columns == ["name"]
        assert database.read_page("empty", 0, 2).rows == []
        assert database.connection is not None
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            database.connection.execute("DROP TABLE empty")
    finally:
        database.close()
    with pytest.raises(ValueError, match="closed"):
        database.read_page("empty", 0, 2)


def test_remote_database_copy_is_removed(database_path: UPath) -> None:
    remote = UPath("memory://browsr-tests/database.sqlite")
    remote.write_bytes(database_path.read_bytes())
    database = SQLiteDatabase(remote)
    assert database.connection is not None
    local_path = Path(database.connection.execute("PRAGMA database_list").fetchone()[2])
    assert local_path.exists()
    assert len(database.read_page("example_view", 0, 10).rows) == 3
    database.close()
    assert not local_path.exists()
    assert remote.exists()
    remote.unlink()


@pytest.mark.parametrize("suffix", [".db", ".db3", ".sqlite", ".SQLITE3"])
@pytest.mark.asyncio
async def test_sqlite_file_routing_and_paging(
    database_path: UPath, suffix: str
) -> None:
    path = database_path.with_suffix(suffix)
    path.write_bytes(database_path.read_bytes())
    app = Browsr(config_object=TextualAppContext(file_path=str(path), max_lines=2))
    async with app.run_test(size=(120, 35)) as pilot:
        switcher = app.code_browser_screen.code_browser.window_switcher
        viewer = switcher.sqlite_window
        assert switcher.get_active_widget() is viewer
        assert viewer.data_table.row_count == 2
        assert viewer.data_table.region.height >= viewer.data_table.row_count + 1
        assert viewer.data_table.get_row_at(0)[1].plain == "[bold]literal[/bold]"
        assert viewer.data_table.get_row_at(1)[1].plain == "NULL"
        assert viewer.data_table.get_row_at(0)[2].plain == "BLOB (2 bytes): 00ff"
        assert viewer.previous_button.disabled is True
        assert viewer.next_button.disabled is False
        await pilot.click("#sqlite-next")
        assert viewer.data_table.row_count == 1
        assert viewer.data_table.get_row_at(0)[0].plain == "3"
        assert viewer.next_button.disabled is True
        await pilot.press("ctrl+left")
        assert viewer.row_offset == 0
        assert viewer.data_table.row_count == 2


@pytest.mark.asyncio
async def test_table_schema_reload_overlays_and_switching(database_path: UPath) -> None:
    app = Browsr(
        config_object=TextualAppContext(file_path=str(database_path), max_lines=2)
    )
    async with app.run_test(size=(120, 35)) as pilot:
        browser = app.code_browser_screen.code_browser
        switcher = browser.window_switcher
        viewer = switcher.sqlite_window
        viewer.selector.value = "example_view"
        await pilot.pause()
        assert viewer.table_name == "example_view"
        assert viewer.data_table.row_count == 2
        assert "CREATE VIEW" in viewer.schema.content.code
        viewer.query_one(TabbedContent).active = "sqlite-schema-tab"
        await pilot.pause()
        assert viewer.schema.visible
        assert viewer.schema.region.height > 0
        browser.toggle_shortcuts()
        assert viewer.display is False
        await pilot.press("escape")
        assert viewer.display is True
        assert switcher.get_active_widget() is viewer
        viewer.selector.value = "empty"
        await pilot.pause()
        assert viewer.data_table.row_count == 0
        assert len(viewer.data_table.columns) == 1
        assert "No rows" in str(viewer.status.content)
        viewer.selector.value = "broken_view"
        await pilot.pause()
        assert "Unable to read" in str(viewer.status.content)
        assert viewer.next_button.disabled
        app.code_browser_screen.action_reload()
        await pilot.pause()
        assert viewer.table_name == 'a weird " table'
        assert viewer.data_table.row_count == 2
        database = viewer.database
        text_path = database_path.parent / "plain.txt"
        text_path.write_text("Hello")
        switcher.render_file(text_path)
        assert switcher.get_active_widget() is switcher.text_window
        assert not viewer.display
        assert database.connection is None


@pytest.mark.parametrize("contents", [None, b"not a SQLite database"])
@pytest.mark.asyncio
async def test_empty_and_invalid_databases(
    tmp_path: Path, contents: bytes | None
) -> None:
    path = tmp_path / "empty.db"
    if contents is None:
        sqlite3.connect(path).close()
    else:
        path.write_bytes(contents)
    app = Browsr(config_object=TextualAppContext(file_path=str(path)))
    async with app.run_test():
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        assert viewer.display
        assert viewer.data_table.row_count == 0
        assert viewer.selector.disabled
        assert viewer.previous_button.disabled
        assert viewer.next_button.disabled
        if contents is None:
            assert "no user tables" in str(viewer.status.content)
        else:
            assert "Unable to open SQLite database" in str(viewer.status.content)


@pytest.mark.asyncio
async def test_database_closed_on_exit(database_path: UPath) -> None:
    app = Browsr(config_object=TextualAppContext(file_path=str(database_path)))
    async with app.run_test():
        database = (
            app.code_browser_screen.code_browser.window_switcher.sqlite_window.database
        )
        assert database.connection is not None
    assert database.connection is None
