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
    window.apply_smart_theme("monokai")
    assert window.theme == "monokai"
    window.apply_smart_theme("invalid-theme")
    assert window.theme == "vscode_dark"  # Default


def test_text_window_language_detection():
    window = TextWindow()
    window.detect_language("test.py")
    assert window.language == "python"
    window.detect_language("test.json")
    assert window.language == "json"


@pytest.mark.asyncio
async def test_window_switcher_routing():
    context = TextualAppContext()
    switcher = WindowSwitcher(config_object=context)

    # Mock UPath for a JSON file
    mock_json = MagicMock(spec=UPath)
    mock_json.suffix = ".json"
    mock_json.suffixes = [".json"]
    mock_json.read_text.return_value = '{"key": "value"}'
    mock_json.__str__.return_value = "test.json"

    # We need to patch various things to avoid NoActiveAppError and other issues
    with patch("textual.widget.Widget.app", new_callable=MagicMock), patch.object(
        switcher.static_window, "file_to_json", return_value='{\n  "key": "value"\n}'
    ), patch.object(switcher.text_window, "scroll_home"), patch.object(
        switcher.vim_scroll, "scroll_home"
    ):
        switcher.render_file(mock_json)
        # JSON should now go to text_window
        assert switcher.get_active_widget() == switcher.text_window
        assert switcher.text_window.display is True
        assert switcher.text_window.language == "json"
