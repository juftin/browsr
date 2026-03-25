from textual.widgets import TextArea

from browsr.widgets.windows import TextWindow


def test_text_window_inheritance():
    window = TextWindow()
    assert isinstance(window, TextArea)
    assert window.read_only is True
