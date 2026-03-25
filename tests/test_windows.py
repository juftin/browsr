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
    assert window.theme == window.default_theme


def test_text_window_theme_mapping():
    window = TextWindow()
    # Test with dark mode
    mock_app = MagicMock()
    mock_app.dark = True
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("textual.widget.Widget.app", mock_app, raising=False)
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
    window.detect_language("test.yml")
    assert window.language == "yaml"
    window.detect_language("test.sh")
    assert window.language == "bash"
    window.detect_language("uv.lock")
    assert window.language == "toml"
    window.detect_language("file.something.json")
    assert window.language == "json"


def test_text_window_linenos():
    window = TextWindow()
    window.linenos = True
    assert window.show_line_numbers is True
    window.linenos = False
    assert window.show_line_numbers is False


def test_text_window_copy_text():
    window = TextWindow()
    window.text = "Hello World"
    mock_app = MagicMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("textual.widget.Widget.app", mock_app, raising=False)
        with patch("pyperclip.copy") as mock_copy:
            # Test no selection
            window.action_copy_text()
            mock_copy.assert_not_called()
            mock_app.notify.assert_called_with(
                title="No Selection",
                message="No text selected to copy",
                severity="warning",
                timeout=1,
            )

            # Test selection
            window.selection = ((0, 0), (0, 5))  # "Hello"
            window.action_copy_text()
            mock_copy.assert_called_with("Hello")
            mock_app.notify.assert_called_with(
                title="Copied",
                message="Selected text copied to clipboard",
                severity="information",
                timeout=1,
            )


@pytest.mark.asyncio
async def test_window_switcher_routing():
    mock_app = MagicMock()
    # Patch the property on the class for the duration of the test
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("textual.widget.Widget.app", mock_app, raising=False)
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)

        # Ensure default theme
        assert switcher.text_window.theme == switcher.text_window.default_theme

        # Mock UPath for a JSON file
        mock_json = MagicMock(spec=UPath)
        mock_json.suffix = ".json"
        mock_json.suffixes = [".json"]
        mock_json.read_text.return_value = '{"key": "value"}'
        mock_json.__str__.return_value = "test.json"

        # Mock UPath for a Python file
        mock_py = MagicMock(spec=UPath)
        mock_py.suffix = ".py"
        mock_py.suffixes = [".py"]
        mock_py.read_text.return_value = "print('hello')"
        mock_py.__str__.return_value = "test.py"

        # We need to patch various things to avoid NoActiveAppError and other issues
        switcher.static_window.file_to_json = MagicMock(
            return_value='{\n  "key": "value"\n}'
        )
        switcher.static_window.file_to_string = MagicMock(return_value="print('hello')")
        switcher.text_window.scroll_home = MagicMock()
        switcher.vim_scroll.scroll_home = MagicMock()

        # Render JSON
        switcher.render_file(mock_json)
        # It was monokai in failure, let's see why
        # If it fails here, I'll add a print to the test
        assert switcher.text_window.theme == switcher.text_window.default_theme

        # Manually change theme
        switcher.text_window.theme = "monokai"

        # Render Python - should PERSIST theme
        switcher.render_file(mock_py)
        assert switcher.text_window.theme == "monokai"


def test_window_switcher_linenos_sync():
    mock_app = MagicMock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("textual.widget.Widget.app", mock_app, raising=False)
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)
        switcher.linenos = True
        assert switcher.static_window.linenos is True
        assert switcher.text_window.linenos is True
        switcher.linenos = False
        assert switcher.static_window.linenos is False
        assert switcher.text_window.linenos is False


def test_window_switcher_theme_sync():
    mock_app = MagicMock()
    mock_app.dark = True
    mock_app.sub_title = ""

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("textual.widget.Widget.app", mock_app, raising=False)
        context = TextualAppContext()
        switcher = WindowSwitcher(config_object=context)
        switcher.rendered_file = "test.py"

        # Test StaticWindow theme cycling
        switcher.switch_window(switcher.static_window)
        initial_theme = switcher.theme
        switcher.next_theme()
        assert switcher.theme != initial_theme
        assert switcher.static_window.theme == switcher.theme

        # Test TextWindow theme cycling
        switcher.switch_window(switcher.text_window)
        initial_text_theme = switcher.text_window.theme
        switcher.next_theme()
        assert switcher.text_window.theme != initial_text_theme
        # Global switcher theme should NOT have changed
        assert switcher.theme == switcher.static_window.theme

        mock_app.dark = False
        # Trigger the watch_dark
        switcher.watch_dark(False)
        # TextWindow forces light theme when app is light
        assert switcher.text_window.theme == "github_light"
