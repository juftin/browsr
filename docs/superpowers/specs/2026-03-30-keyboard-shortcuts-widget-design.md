# Design Spec: Keyboard Shortcuts Widget

## Summary
Create a `ShortcutsWindow` and `ShortcutsPopUp` widget to display active keyboard shortcuts in `browsr`. This widget will follow the established `ConfirmationWindow` pattern but focus on dynamic shortcut discovery using modern Textual practices.

## Context
Users often need a quick reference for available keyboard shortcuts without leaving the application. A popup window triggered by `?` provides a non-intrusive way to surface this information.

## Goals
- Display all currently active keyboard shortcuts (Global, Screen-level, and Widget-level).
- Match the visual style of the existing `ConfirmationPopUp`.
- Ensure the information is always up-to-date and deduplicated using dynamic discovery.

## Non-Goals
- Allowing users to remap keys within this widget.
- Supporting complex filtering or searching of shortcuts.

## Architecture
The implementation will follow the `ConfirmationWindow` pattern in `browsr/widgets/` for consistency with existing overlays, but will utilize `active_bindings` for robust shortcut discovery.

### Components
1. **`ShortcutsPopUp(Container)`**:
   - Resides in `browsr/widgets/shortcuts.py`.
   - Contains a header (`Static`), a `DataTable` for displaying shortcuts, and a "Close" button.
   - Responsible for shortcut discovery and filtering.
2. **`ShortcutsWindow(Container)`**:
   - Resides in `browsr/widgets/shortcuts.py`.
   - Acts as a full-screen overlay (`width: 100%; height: 100%`).
   - Centers the `ShortcutsPopUp` using `align: center middle`.

### Data Flow
1. **Trigger**: User presses `?` (bound in `Browsr.BINDINGS`).
2. **Discovery**:
   - `ShortcutsPopUp` accesses `self.app.active_bindings` to gather all currently active shortcuts.
   - This automatically handles precedence (Widget > Screen > App) and deduplication.
3. **Filtering & Rendering**:
   - Filter out bindings where `show=False`.
   - Populates a read-only `DataTable` with two columns: **Key** and **Description**.
4. **Closing**:
   - The window is hidden when the user clicks "Close" or presses `Esc`/`q`.

## UI/UX Design
- **Header**: "Keyboard Shortcuts" (Centered, Bold).
- **Body**: `DataTable` with columns for "Key" and "Description".
- **Footer**: "Close" button (Standard variant).
- **Styling**:
  - Uses `$boost` for background and `wide $primary` for borders.
  - Matches `ConfirmationPopUp` aesthetic in `browsr.css`.

## Testing Plan
- **Manual Verification**:
  - Open `browsr`.
  - Trigger the shortcuts window with `?`.
  - Verify that active shortcuts for the current context are accurately listed.
  - Test closing the window via button and keyboard (`Esc`, `q`).
- **Automated Tests**:
  - **Unit Test**: Verify `ShortcutsPopUp` discovery logic with mock bindings.
  - **Integration Test**: Use `App.run_test()` to simulate `?` and assert the visibility of the shortcuts window.
  - **Snapshot Test**: Add a visual regression test in `tests/test_screenshots.py`.
