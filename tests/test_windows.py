from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import TextArea
from textual_universal_directorytree import UPath

from browsr.base import TextualAppContext
from browsr.widgets.windows import TextWindow, WindowSwitcher


def test_text_window_inheritance():
    window = TextWindow()
    assert isinstance(window, TextArea)
    assert window.read_only is True


def test_text_window_theme_mapping():
    window = TextWindow()
    # Test with dark mode
    with patch("textual.widget.Widget.app", new_callable=MagicMock) as mock_app:
        mock_app.dark = True
        window.apply_smart_theme("monokai")
        assert window.theme == "monokai"
        window.apply_smart_theme("invalid-theme")
        assert window.theme == "vscode_dark"  # Default

        # Test with light mode
        mock_app.dark = False
        window.apply_smart_theme("monokai")
        assert window.theme == "github_light"


def test_text_window_language_detection():
    window = TextWindow()
    window.detect_language("test.py")
    assert window.language == "python"
    window.detect_language("test.json")
    assert window.language == "json"


def test_text_window_linenos():
    window = TextWindow()
    window.linenos = True
    assert window.show_line_numbers is True
    window.linenos = False
    assert window.show_line_numbers is False


@pytest.mark.asyncio
async def test_window_switcher_routing():
    # We need to patch before init because watch_theme is called on init
    with patch("textual.widget.Widget.app", new_callable=MagicMock):
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)

        # Mock UPath for a JSON file
        mock_json = MagicMock(spec=UPath)
        mock_json.suffix = ".json"
        mock_json.suffixes = [".json"]
        mock_json.read_text.return_value = '{"key": "value"}'
        mock_json.__str__.return_value = "test.json"

        # We need to patch various things to avoid NoActiveAppError and other issues
        with patch.object(
            switcher.static_window,
            "file_to_json",
            return_value='{\n  "key": "value"\n}',
        ), patch.object(switcher.text_window, "scroll_home"), patch.object(
            switcher.vim_scroll, "scroll_home"
        ):
            switcher.render_file(mock_json)
            # JSON should now go to text_window
            assert switcher.get_active_widget() == switcher.text_window
            assert switcher.text_window.display is True
            assert switcher.text_window.language == "json"


def test_window_switcher_linenos_sync():
    with patch("textual.widget.Widget.app", new_callable=MagicMock):
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)
        switcher.linenos = True
        assert switcher.static_window.linenos is True
        assert switcher.text_window.linenos is True
        switcher.linenos = False
        assert switcher.static_window.linenos is False
        assert switcher.text_window.linenos is False


def test_window_switcher_theme_sync():
    with patch("textual.widget.Widget.app", new_callable=MagicMock) as mock_app:
        mock_app.dark = True
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)

        switcher.theme = "monokai"
        assert switcher.static_window.theme == "monokai"
        assert switcher.text_window.theme == "monokai"

        mock_app.dark = False
        # Trigger the watch_dark
        switcher.watch_dark(False)
        assert (
            switcher.text_window.theme == "github_light"
        )  # TextWindow forces light theme when app is light
        assert (
            switcher.static_window.theme == "monokai"
        )  # StaticWindow keeps Browsr theme
