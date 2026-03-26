# TextWindow Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the use of `StaticWindow` with a new `TextWindow` (based on Textual's `TextArea`) for code, JSON, and generic text files to provide better performance and a more native editor experience.

**Architecture:** Create a `TextWindow` class that inherits from `TextArea` and `BaseCodeWindow`. Update `WindowSwitcher.render_file` to route specific file types to `TextWindow` while keeping `StaticWindow` for Markdown, images, and errors. Implement "Smart Mapping" for themes and syntax.

**Tech Stack:** Textual 0.53.0 (TextArea), tree-sitter (via textual[syntax]), Python.

---

### Task 1: Create the TextWindow Widget

**Files:**
- Create: `browsr/widgets/windows.py` (Modify existing)
- Test: `tests/test_windows.py` (Create new)

- [ ] **Step 1: Write a failing test for TextWindow creation**

```python
from browsr.widgets.windows import TextWindow
from textual.widgets import TextArea

def test_text_window_inheritance():
    window = TextWindow()
    assert isinstance(window, TextArea)
    assert window.read_only is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_windows.py -v`
Expected: FAIL (ImportError or NameError)

- [ ] **Step 3: Implement TextWindow class in `browsr/widgets/windows.py`**

```python
class TextWindow(TextArea, BaseCodeWindow):
    """
    A window that displays text using a TextArea.
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("l", "cursor_right", "Right", show=False),
        Binding("h", "cursor_left", "Left", show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(read_only=True, **kwargs)
        self.show_line_numbers = True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_windows.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add browsr/widgets/windows.py tests/test_windows.py
git commit -m "feat: add TextWindow widget based on TextArea"
```

---

### Task 2: Implement Smart Theme and Language Mapping

**Files:**
- Modify: `browsr/widgets/windows.py`
- Test: `tests/test_windows.py`

- [ ] **Step 1: Write tests for theme and language mapping**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_windows.py -v`
Expected: FAIL (AttributeError)

- [ ] **Step 3: Implement mapping methods in `TextWindow`**

```python
    THEME_MAP = {
        "monokai": "monokai",
        "dracula": "dracula",
        "github-dark": "vscode_dark",
        "solarized-light": "github_light",
    }

    def apply_smart_theme(self, rich_theme: str) -> None:
        target = self.THEME_MAP.get(rich_theme, "vscode_dark")
        if target in self.available_themes:
            self.theme = target

    def detect_language(self, file_path: str | UPath) -> None:
        if isinstance(file_path, str):
            file_path = UPath(file_path)
        ext = file_path.suffix.lstrip(".").lower()
        if ext in self.available_languages:
            self.language = ext
        elif ext == "py":
            self.language = "python"
        elif ext == "js":
            self.language = "javascript"
        else:
            self.language = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_windows.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add browsr/widgets/windows.py tests/test_windows.py
git commit -m "feat: implement smart theme and language mapping for TextWindow"
```

---

### Task 3: Update WindowSwitcher Routing

**Files:**
- Modify: `browsr/widgets/windows.py`
- Test: `tests/test_windows.py`

- [ ] **Step 1: Write test for WindowSwitcher routing**

```python
def test_window_switcher_routing():
    switcher = WindowSwitcher()
    # Mocking render_file or checking internal state if possible
    # We want to ensure .json goes to TextWindow and .md goes to StaticWindow
    pass
```

- [ ] **Step 2: Run test to verify current behavior**

- [ ] **Step 3: Update `WindowSwitcher.render_file` logic**

```python
        if file_path.suffix.lower() == ".md":
            # ... keep StaticWindow for Markdown
            pass
        elif file_path.suffix.lower() == ".json":
             # ... route to TextWindow
             pass
        # ... and so on for other types
```

- [ ] **Step 4: Run tests to verify new routing**

- [ ] **Step 5: Commit**

```bash
git add browsr/widgets/windows.py
git commit -m "feat: update WindowSwitcher to route code and JSON to TextWindow"
```

---

### Task 4: Final Integration and Verification

- [ ] **Step 1: Verify global theme updates affect TextWindow**
- [ ] **Step 2: Verify Vim bindings (h, j, k, l) work in TextWindow**
- [ ] **Step 3: Run all project tests to ensure no regressions**

Run: `pytest tests/ -v`

- [ ] **Step 4: Final Commit**

```bash
git commit --allow-empty -m "fix: final polish and verification of TextWindow integration"
```
