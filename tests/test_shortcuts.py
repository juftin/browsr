from typing import ClassVar
from unittest.mock import MagicMock

import pytest
from textual.app import App
from textual.binding import Binding
from textual_universal_directorytree import UPath

from browsr.base import TextualAppContext
from browsr.browsr import Browsr
from browsr.widgets.confirmation import ConfirmationPopUp
from browsr.widgets.shortcuts import ShortcutsPopUp


class MockApp(App):
    BINDINGS: ClassVar[list[Binding]] = [Binding("q", "quit", "Quit")]


@pytest.mark.asyncio
async def test_shortcut_discovery():
    app = MockApp()
    async with app.run_test():
        popup = ShortcutsPopUp()
        await app.mount(popup)
        # Note: the widget calls update_shortcuts on mount
        table = popup.query_one("#shortcuts-table")
        assert table.row_count > 0


@pytest.mark.asyncio
async def test_shortcuts_overlay_is_mounted_in_code_browser(repo_dir: UPath):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test() as pilot:
        await pilot.press("question_mark")

        shortcuts_window = app.code_browser_screen.code_browser.shortcuts_window
        assert shortcuts_window.display is True
        assert shortcuts_window.parent is app.code_browser_screen.code_browser


@pytest.mark.asyncio
async def test_shortcuts_popup_stays_within_viewport(
    github_release_path: UPath,
):
    app = Browsr(config_object=TextualAppContext(file_path=github_release_path))

    async with app.run_test(size=(30, 15)) as pilot:
        await pilot.press("question_mark")
        await pilot.pause()

        popup = app.code_browser_screen.code_browser.shortcuts
        shortcuts_window = app.code_browser_screen.code_browser.shortcuts_window
        viewport = app.size

        assert shortcuts_window.display is True
        assert shortcuts_window.region.x >= 0
        assert shortcuts_window.region.y >= 0
        assert shortcuts_window.region.right <= viewport.width
        assert shortcuts_window.region.bottom <= viewport.height
        assert popup.region.x >= 0
        assert popup.region.y >= 0


@pytest.mark.asyncio
async def test_shortcuts_escape_restores_text_window(repo_dir: UPath):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test() as pilot:
        code_browser = app.code_browser_screen.code_browser
        code_browser.window_switcher.vim_scroll.display = False
        code_browser.window_switcher.datatable_window.display = False
        code_browser.window_switcher.text_window.display = True

        code_browser.toggle_shortcuts()

        assert code_browser.shortcuts_window.display is True
        assert code_browser.window_switcher.text_window.display is False

        await pilot.press("escape")

        assert code_browser.shortcuts_window.display is False
        assert code_browser.window_switcher.text_window.display is True
        assert code_browser.window_switcher.vim_scroll.display is False
        assert code_browser.window_switcher.datatable_window.display is False


@pytest.mark.asyncio
async def test_download_confirmation_restores_text_window(
    repo_dir: UPath, monkeypatch: pytest.MonkeyPatch
):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test():
        code_browser = app.code_browser_screen.code_browser
        selected_file_path = MagicMock()
        selected_file_path.is_dir.return_value = False
        selected_file_path.name = "example.txt"
        selected_file_path.__str__.return_value = "github://owner:repo/example.txt"

        monkeypatch.setattr(
            "browsr.widgets.code_browser.is_remote_path", lambda _: True
        )
        monkeypatch.setattr(
            code_browser,
            "_get_download_file_name",
            lambda: repo_dir / "downloaded-example.txt",
        )

        code_browser.selected_file_path = selected_file_path
        code_browser.window_switcher.vim_scroll.display = False
        code_browser.window_switcher.datatable_window.display = False
        code_browser.window_switcher.text_window.display = True

        code_browser.download_file_workflow()

        assert code_browser.confirmation_window.display is True
        assert code_browser.window_switcher.text_window.display is False

        code_browser.handle_confirmation_window_display_toggle(
            ConfirmationPopUp.DisplayToggle()
        )

        assert code_browser.window_switcher.text_window.display is True
        assert code_browser.window_switcher.vim_scroll.display is False
        assert code_browser.window_switcher.datatable_window.display is False


@pytest.mark.asyncio
async def test_shortcuts_and_confirmation_can_switch_back_and_forth(
    repo_dir: UPath, monkeypatch: pytest.MonkeyPatch
):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test():
        code_browser = app.code_browser_screen.code_browser
        selected_file_path = MagicMock()
        selected_file_path.is_dir.return_value = False
        selected_file_path.name = "example.txt"
        selected_file_path.__str__.return_value = "github://owner:repo/example.txt"

        monkeypatch.setattr(
            "browsr.widgets.code_browser.is_remote_path", lambda _: True
        )
        monkeypatch.setattr(
            code_browser,
            "_get_download_file_name",
            lambda: repo_dir / "downloaded-example.txt",
        )

        code_browser.selected_file_path = selected_file_path
        code_browser.window_switcher.vim_scroll.display = False
        code_browser.window_switcher.datatable_window.display = False
        code_browser.window_switcher.text_window.display = True

        code_browser.toggle_shortcuts()
        assert code_browser.shortcuts_window.display is True
        assert code_browser.confirmation_window.display is False

        code_browser.download_file_workflow()
        assert code_browser.shortcuts_window.display is False
        assert code_browser.confirmation_window.display is True
        assert code_browser.window_switcher.text_window.display is False

        code_browser.toggle_shortcuts()
        assert code_browser.shortcuts_window.display is True
        assert code_browser.confirmation_window.display is False
        assert code_browser.window_switcher.text_window.display is False

        code_browser.toggle_shortcuts()
        assert code_browser.shortcuts_window.display is False
        assert code_browser.confirmation_window.display is True

        code_browser.download_file_workflow()
        assert code_browser.shortcuts_window.display is False
        assert code_browser.confirmation_window.display is False
        assert code_browser.window_switcher.text_window.display is True


@pytest.mark.asyncio
async def test_download_confirmation_popup_stays_within_viewport(
    repo_dir: UPath, monkeypatch: pytest.MonkeyPatch
):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test(size=(30, 15)) as pilot:
        code_browser = app.code_browser_screen.code_browser
        selected_file_path = MagicMock()
        selected_file_path.is_dir.return_value = False
        selected_file_path.name = "example.txt"
        selected_file_path.__str__.return_value = "github://owner:repo/example.txt"

        monkeypatch.setattr(
            "browsr.widgets.code_browser.is_remote_path", lambda _: True
        )
        monkeypatch.setattr(
            code_browser,
            "_get_download_file_name",
            lambda: repo_dir / "downloaded-example.txt",
        )

        code_browser.selected_file_path = selected_file_path
        code_browser.download_file_workflow()
        await pilot.pause()

        popup = code_browser.confirmation
        confirmation_window = code_browser.confirmation_window
        viewport = app.size

        assert confirmation_window.display is True
        assert confirmation_window.region.x >= 0
        assert confirmation_window.region.y >= 0
        assert confirmation_window.region.right <= viewport.width
        assert confirmation_window.region.bottom <= viewport.height
        assert popup.region.x >= 0
        assert popup.region.y >= 0


@pytest.mark.asyncio
async def test_download_confirmation_escape_restores_text_window(
    repo_dir: UPath, monkeypatch: pytest.MonkeyPatch
):
    app = Browsr(config_object=TextualAppContext(file_path=repo_dir))

    async with app.run_test() as pilot:
        code_browser = app.code_browser_screen.code_browser
        selected_file_path = MagicMock()
        selected_file_path.is_dir.return_value = False
        selected_file_path.name = "example.txt"
        selected_file_path.__str__.return_value = "github://owner:repo/example.txt"

        monkeypatch.setattr(
            "browsr.widgets.code_browser.is_remote_path", lambda _: True
        )
        monkeypatch.setattr(
            code_browser,
            "_get_download_file_name",
            lambda: repo_dir / "downloaded-example.txt",
        )

        code_browser.selected_file_path = selected_file_path
        code_browser.window_switcher.vim_scroll.display = False
        code_browser.window_switcher.datatable_window.display = False
        code_browser.window_switcher.text_window.display = True

        code_browser.download_file_workflow()

        assert code_browser.confirmation_window.display is True
        assert code_browser.window_switcher.text_window.display is False

        await pilot.press("escape")

        assert code_browser.confirmation_window.display is False
        assert code_browser.window_switcher.text_window.display is True
        assert code_browser.window_switcher.vim_scroll.display is False
        assert code_browser.window_switcher.datatable_window.display is False
