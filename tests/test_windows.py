from textual.widgets import TextArea

from browsr.widgets.windows import TextWindow


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
