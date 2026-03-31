# Design Spec: Keyboard Shortcuts Widget

## Summary
Create a `ShortcutsWindow` and `ShortcutsPopUp` widget to display active keyboard shortcuts in `browsr`. This widget will follow the established `ConfirmationWindow` pattern but focus on dynamic shortcut discovery.

## Context
Users often need a quick reference for available keyboard shortcuts without leaving the application. A popup window triggered by `?` or a similar key provides a non-intrusive way to surface this information.

## Goals
- Display all currently active keyboard shortcuts (Global, Screen-level, and Widget-level).
- Match the visual style of the existing `ConfirmationPopUp`.
- Ensure the information is always up-to-date by using dynamic discovery.

## Non-Goals
- Allowing users to remap keys within this widget.
- Supporting complex filtering or searching of shortcuts.

## Architecture
The implementation will follow the `ConfirmationWindow` pattern in `browsr/widgets/`.

### Components
1. **`ShortcutsPopUp(Container)`**:
   - Resides in `browsr/widgets/shortcuts.py`.
   - Contains a header (`Static`), a scrollable list of shortcuts, and a "Close" button.
   - Responsible for shortcut discovery.
2. **`ShortcutsWindow(Container)`**:
   - Resides in `browsr/widgets/shortcuts.py`.
   - Acts as a full-screen overlay (`width: 100%; height: 100%`).
   - Centers the `ShortcutsPopUp`.

### Data Flow
1. **Trigger**: User presses a designated key (e.g., `?`).
2. **Discovery**:
   - `ShortcutsPopUp` accesses `self.app.screen.bindings` for screen-level shortcuts.
   - `ShortcutsPopUp` accesses `self.app.focused.bindings` for widget-level shortcuts (if a widget is focused).
   - `ShortcutsPopUp` accesses `self.app.bindings` for app-level shortcuts.
3. **Rendering**:
   - The discovered bindings are filtered to exclude `show=False` bindings.
   - The key name and description are rendered in a clean, tabular format (likely using a vertical `Container` of `Static` rows or a `DataTable`).
4. **Closing**:
   - The window is hidden when the user clicks "Close" or presses `Esc`/`q`.

## UI/UX Design
- **Header**: "Keyboard Shortcuts" (Centered, Bold).
- **Body**: Two columns (Key, Description).
- **Footer**: "Close" button (Standard variant).
- **Styling**: Leverages `browsr.css` for consistent borders, padding, and background colors.

## Testing Plan
- **Manual Verification**:
  - Open `browsr`.
  - Trigger the shortcuts window.
  - Verify that shortcuts for the current screen (e.g., Code Browser) are listed.
  - Verify that global shortcuts (e.g., Quit) are listed.
  - Test closing the window via button and keyboard.
- **Automated Tests**:
  - Add a test case in `tests/test_windows.py` (or a new `tests/test_shortcuts.py`) to verify that `ShortcutsPopUp` correctly discovers bindings from a mock application state.
