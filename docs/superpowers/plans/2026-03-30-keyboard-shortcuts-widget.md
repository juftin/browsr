# Keyboard Shortcuts Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a `ShortcutsWindow` and `ShortcutsPopUp` widget that dynamically discovers and displays all active keyboard shortcuts in the `browsr` application.

**Architecture:** Create a new module `browsr/widgets/shortcuts.py` containing the `ShortcutsPopUp` (the UI) and `ShortcutsWindow` (the container). Use `self.app.active_bindings` for dynamic shortcut discovery and a `DataTable` for display.

**Tech Stack:** Python, Textual, Rich.

---

### Task 1: Create the Shortcuts Widgets

**Files:**
- Create: `browsr/widgets/shortcuts.py`
- Modify: `browsr/browsr.css`

- [ ] **Step 1: Create the shortcuts module with basic structure**

```python
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, DataTable, Static

class ShortcutsPopUp(Container):
    """A Pop Up that displays keyboard shortcuts"""
    def compose(self) -> ComposeResult:
        yield Static("Keyboard Shortcuts", id="shortcuts-header")
        yield DataTable(id="shortcuts-table")
        yield Button("Close", variant="primary", id="close-shortcuts")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Key", "Description")
        self.update_shortcuts()

    def update_shortcuts(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for binding in self.app.active_bindings:
            if binding.show:
                table.add_row(binding.key, binding.description)

class ShortcutsWindow(Container):
    """Window containing the Shortcuts Pop Up"""
    def compose(self) -> ComposeResult:
        yield ShortcutsPopUp()
```

- [ ] **Step 2: Add styling to `browsr/browsr.css`**

```css
/* -- ShortcutsPopUp -- */

ShortcutsWindow {
    width: 100%;
    height: 100%;
    align: center middle;
    display: none;
}

ShortcutsPopUp {
    background: $boost;
    height: auto;
    max-height: 80%;
    max-width: 80;
    min-width: 40;
    border: wide $primary;
    padding: 1 2;
    margin: 1 2;
    box-sizing: border-box;
}

#shortcuts-header {
    width: 100%;
    content-align: center middle;
    text-style: bold;
    margin-bottom: 1;
}

#shortcuts-table {
    height: auto;
    max-height: 20;
    border: none;
}

ShortcutsPopUp Button {
    margin-top: 1;
    width: 100%;
}
```

- [ ] **Step 3: Commit**

```bash
git add browsr/widgets/shortcuts.py browsr/browsr.css
git commit -m "✨ (widgets): Add ShortcutsWindow and ShortcutsPopUp widgets"
```

---

### Task 2: Integrate Shortcuts into CodeBrowser

**Files:**
- Modify: `browsr/widgets/code_browser.py`

- [ ] **Step 1: Import and instantiate the shortcuts window**

```python
from browsr.widgets.shortcuts import ShortcutsWindow
# ... in __init__
self.shortcuts_window = ShortcutsWindow(id="shortcuts-container")
```

- [ ] **Step 2: Add to `compose`**

```python
# ... in compose
yield self.shortcuts_window
```

- [ ] **Step 3: Add binding for `?`**

```python
# ... in bind_keys
self.app.bind(keys="?", action="toggle_shortcuts", description="Shortcuts", show=True)
```

- [ ] **Step 4: Implement `action_toggle_shortcuts`**

```python
def action_toggle_shortcuts(self) -> None:
    self.shortcuts_window.display = not self.shortcuts_window.display
    if self.shortcuts_window.display:
        self.shortcuts_window.query_one(ShortcutsPopUp).update_shortcuts()
        self.shortcuts_window.focus()
```

- [ ] **Step 5: Commit**

```bash
git add browsr/widgets/code_browser.py
git commit -m "✨ (code-browser): Integrate shortcuts window"
```

---

### Task 3: Testing and Verification

**Files:**
- Create: `tests/test_shortcuts.py`

- [ ] **Step 1: Write a test for shortcut discovery**

```python
import pytest
from textual.app import App
from browsr.widgets.shortcuts import ShortcutsPopUp

class MockApp(App):
    BINDINGS = [("q", "quit", "Quit")]

@pytest.mark.asyncio
async def test_shortcut_discovery():
    app = MockApp()
    async with app.run_test() as pilot:
        popup = ShortcutsPopUp()
        await app.mount(popup)
        popup.update_shortcuts()
        table = popup.query_one("#shortcuts-table")
        assert table.row_count > 0
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_shortcuts.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_shortcuts.py
git commit -m "✅ (tests): Add tests for shortcuts widget"
```
