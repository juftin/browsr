"""SQLite access and integration with the browser's file previews."""

import json
import sqlite3
from pathlib import Path

import pyperclip
import pytest
from textual.widgets import DataTable
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
        await pilot.press("left_curly_bracket")
        assert viewer.row_offset == 0
        assert viewer.data_table.row_count == 2


@pytest.mark.asyncio
async def test_table_reload_overlays_and_switching(database_path: UPath) -> None:
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


@pytest.mark.parametrize("focus_target", ["data_table", "selector"])
@pytest.mark.asyncio
async def test_table_shortcuts_wrap_reset_paging_and_preserve_focus(
    database_path: UPath, focus_target: str
) -> None:
    app = Browsr(
        config_object=TextualAppContext(file_path=str(database_path), max_lines=2)
    )
    async with app.run_test(size=(140, 35)) as pilot:
        browser = app.code_browser_screen.code_browser
        viewer = browser.window_switcher.sqlite_window
        focused_widget = getattr(viewer, focus_target)
        focused_widget.focus()
        await pilot.press("right_curly_bracket")
        assert viewer.row_offset == 2

        await pilot.press("left_square_bracket")
        assert viewer.table_name == viewer.selector.value == "example_view"
        assert viewer.row_offset == 0
        assert viewer.data_table.row_count == 2
        assert app.focused is focused_widget

        await pilot.press("right_square_bracket")
        assert viewer.table_name == viewer.selector.value == 'a weird " table'
        assert viewer.data_table.get_row_at(0)[0].plain == "1"
        await pilot.press("right_square_bracket")
        assert viewer.table_name == viewer.selector.value == "broken_view"
        assert "Unable to read" in str(viewer.status.content)
        await pilot.press("right_square_bracket")
        assert viewer.table_name == viewer.selector.value == "empty"
        assert viewer.data_table.row_count == 0
        await pilot.press("right_square_bracket")
        assert viewer.table_name == viewer.selector.value == "example_view"
        assert viewer.data_table.row_count == 2
        assert app.focused is focused_widget

        await pilot.press("question_mark")
        shortcuts = browser.shortcuts.query_one(DataTable)
        rows = [shortcuts.get_row_at(index) for index in range(shortcuts.row_count)]
        assert ["[", "Previous Table"] in rows
        assert ["]", "Next Table"] in rows
        assert ["{", "Previous Page"] in rows
        assert ["}", "Next Page"] in rows
        assert ["c", "Copy Cell"] in rows
        assert ["shift+c", "Copy Row"] in rows


@pytest.mark.asyncio
async def test_table_shortcuts_preserve_page_for_single_table(tmp_path: Path) -> None:
    path = tmp_path / "single.db"
    connection = sqlite3.connect(path)
    with connection:
        connection.execute("CREATE TABLE numbers (value INTEGER)")
        connection.executemany("INSERT INTO numbers VALUES (?)", [(1,), (2,)])
    connection.close()
    app = Browsr(config_object=TextualAppContext(file_path=str(path), max_lines=1))
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        viewer.data_table.focus()
        await pilot.press(
            "right_curly_bracket", "left_square_bracket", "right_square_bracket"
        )
        assert viewer.table_name == viewer.selector.value == "numbers"
        assert viewer.row_offset == 1
        assert viewer.data_table.get_row_at(0)[0].plain == "2"


@pytest.mark.asyncio
async def test_bounded_columns_copy_full_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "long-values.db"
    column_name = "long column " + "長" * 40
    value = "line one\nline two\ttab\rcarriage return " + "界" * 80
    blob = bytes(range(100))
    connection = sqlite3.connect(path)
    with connection:
        connection.execute(
            f'CREATE TABLE entries (id INTEGER, "{column_name}" TEXT, '
            "missing TEXT, payload BLOB, price REAL)"
        )
        connection.execute(
            "INSERT INTO entries VALUES (?, ?, ?, ?, ?)",
            (1, value, None, blob, 1.25),
        )
    connection.close()
    copied: list[str] = []
    monkeypatch.setattr(pyperclip, "copy", copied.append)
    app = Browsr(config_object=TextualAppContext(file_path=str(path)))
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        table = viewer.data_table
        table.focus()
        assert all(column.width <= 40 for column in table.columns.values())
        assert all(column.label.cell_len <= 40 for column in table.columns.values())
        cells = table.get_row_at(0)
        assert all(cell.cell_len <= 40 for cell in cells)
        assert cells[1].plain.endswith("…")
        assert "\\n" in cells[1].plain
        assert "\n" not in cells[1].plain
        assert cells[3].plain.endswith("…")
        table.move_cursor(column=1)
        await pilot.press("c")
        assert copied[-1] == value
        table.move_cursor(column=3)
        await pilot.press("c")
        assert copied[-1] == blob.hex()
        table.move_cursor(column=2)
        await pilot.press("c")
        assert copied[-1] == "NULL"
        table.move_cursor(column=4)
        await pilot.press("c")
        assert copied[-1] == "1.25"
        table.move_cursor(column=0)
        await pilot.press("c", "C")
        assert copied[-2] == "1"
        assert len(copied) == 6
        assert json.loads(copied[-1]) == {
            "id": 1,
            column_name: value,
            "missing": None,
            "payload": {"type": "blob", "hex": blob.hex()},
            "price": 1.25,
        }


@pytest.mark.asyncio
async def test_copy_row_tracks_selection_pages_and_tables(
    database_path: UPath, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied: list[str] = []
    monkeypatch.setattr(pyperclip, "copy", copied.append)
    app = Browsr(
        config_object=TextualAppContext(file_path=str(database_path), max_lines=2)
    )
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        viewer.data_table.focus()
        await pilot.press("down", "C")
        assert json.loads(copied[-1]) == {
            "id": 2,
            "value": None,
            "data": {"type": "blob", "hex": ""},
        }
        await pilot.press("right_curly_bracket", "C")
        assert json.loads(copied[-1]) == {"id": 3, "value": 1.5, "data": None}
        await pilot.press("right_square_bracket", "C")
        assert viewer.table_name == "broken_view"
        assert len(copied) == 2
        await pilot.press("right_square_bracket", "C")
        assert viewer.table_name == "empty"
        assert len(copied) == 2
        await pilot.press("right_square_bracket", "C")
        assert viewer.table_name == "example_view"
        assert json.loads(copied[-1]) == {
            "id": 1,
            "value": "[bold]literal[/bold]",
            "data": {"type": "blob", "hex": "00ff"},
        }


@pytest.mark.asyncio
async def test_copy_cell_tracks_selection_pages_and_tables(
    database_path: UPath, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied: list[str] = []
    monkeypatch.setattr(pyperclip, "copy", copied.append)
    app = Browsr(
        config_object=TextualAppContext(file_path=str(database_path), max_lines=2)
    )
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        viewer.data_table.focus()
        await pilot.press("down", "right", "c")
        assert copied == ["NULL"]
        await pilot.press("right", "c")
        assert copied[-1] == ""
        await pilot.press("right_curly_bracket", "right", "c")
        assert copied[-1] == "1.5"
        await pilot.press("right_square_bracket", "c")
        assert viewer.table_name == "broken_view"
        assert len(copied) == 3
        await pilot.press("right_square_bracket", "c")
        assert viewer.table_name == "empty"
        assert len(copied) == 3
        await pilot.press("right_square_bracket", "right", "c")
        assert viewer.table_name == "example_view"
        assert copied[-1] == "[bold]literal[/bold]"


@pytest.mark.parametrize("copy_key", ["c", "C"])
@pytest.mark.asyncio
async def test_copy_uses_terminal_clipboard_when_system_clipboard_is_unavailable(
    database_path: UPath, monkeypatch: pytest.MonkeyPatch, copy_key: str
) -> None:
    def unavailable_clipboard(_: str) -> None:
        raise pyperclip.PyperclipException("No system clipboard")

    monkeypatch.setattr(pyperclip, "copy", unavailable_clipboard)
    app = Browsr(config_object=TextualAppContext(file_path=str(database_path)))
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        viewer.data_table.focus()
        await pilot.press("right", copy_key)
        if copy_key == "c":
            assert app.clipboard == "[bold]literal[/bold]"
        else:
            assert json.loads(app.clipboard) == {
                "id": 1,
                "value": "[bold]literal[/bold]",
                "data": {"type": "blob", "hex": "00ff"},
            }


@pytest.mark.parametrize("focus_context", ["tree", "confirmation"])
@pytest.mark.asyncio
async def test_sqlite_help_lists_all_shortcuts_outside_viewer_focus(
    database_path: UPath, focus_context: str
) -> None:
    app = Browsr(config_object=TextualAppContext(file_path=str(database_path)))
    async with app.run_test(size=(140, 35)) as pilot:
        browser = app.code_browser_screen.code_browser
        browser.show_tree = True
        if focus_context == "tree":
            browser.directory_tree.focus()
        else:
            browser._show_overlay(browser.confirmation_window)
        await pilot.press("question_mark")
        shortcuts = browser.shortcuts.query_one(DataTable)
        rows = [shortcuts.get_row_at(index) for index in range(shortcuts.row_count)]
        expected = [
            ["c", "Copy Cell"],
            ["shift+c", "Copy Row"],
            ["{", "Previous Page"],
            ["}", "Next Page"],
            ["[", "Previous Table"],
            ["]", "Next Table"],
        ]
        assert all(row in rows for row in expected)
        assert len({row[0] for row in rows}) == len(rows)
        browser.toggle_shortcuts()
        if focus_context == "confirmation":
            browser._close_overlay(browser.confirmation_window)
        text_path = database_path.parent / "plain.txt"
        text_path.write_text("Hello")
        browser.window_switcher.render_file(text_path)
        browser.directory_tree.focus()
        await pilot.press("question_mark")
        rows = [shortcuts.get_row_at(index) for index in range(shortcuts.row_count)]
        assert all(row not in rows for row in expected)


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
    async with app.run_test() as pilot:
        viewer = app.code_browser_screen.code_browser.window_switcher.sqlite_window
        viewer.focus()
        await pilot.press("left_square_bracket", "right_square_bracket")
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
