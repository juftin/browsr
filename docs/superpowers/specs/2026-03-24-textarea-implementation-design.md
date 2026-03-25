# Design Spec: TextWindow Integration with TextArea

- **Date:** 2026-03-24
- **Topic:** Replacing StaticWindow with TextArea for code/text files in Browsr

## 1. Goal
Introduce a new `TextWindow` widget based on Textual's `TextArea` to provide a higher-performance, editor-like experience for viewing code and text files, while maintaining `StaticWindow` for specialized Rich rendering (Markdown, Images, Exceptions).

## 2. Architecture

### 2.1 The `TextWindow` Widget
- **Inheritance:** `class TextWindow(TextArea, BaseCodeWindow)`
- **Configuration:** Initialized as `read_only=True` and `soft_wrap=False`.
- **Vim Bindings:** Native Vim navigation bindings (`h`, `j`, `k`, `l`) added directly to the `BINDINGS` list, mapping to `TextArea`'s internal cursor actions (`cursor_left`, `cursor_down`, `cursor_up`, `cursor_right`).
- **Scrolling:** Leverages `TextArea`'s built-in high-performance scrolling.

### 2.2 WindowSwitcher Routing Logic
The `WindowSwitcher` will be updated to route files as follows:

- **DataTableWindow:** `.csv`, `.parquet`, `.feather`
- **StaticWindow:**
    - Markdown (`.md`)
    - Images
    - Exceptions/Errors (using ASCII art)
- **TextWindow (NEW):**
    - JSON (`.json`)
    - All other code files (Python, JS, etc.)
    - Generic text files

### 2.3 Syntax & Theme Intelligence
- **Syntax Detection:** Map file extensions to `TextArea.available_languages` (tree-sitter based).
- **Theme Mapping:** Map Browsr's Rich-based themes to the closest `TextArea.available_themes` equivalents (e.g., `monokai` -> `monokai`, `dracula` -> `dracula`, `github-dark` -> `vscode_dark`).
- **Reactive Updates:** `TextWindow` will watch the global application theme and update its internal `theme` attribute accordingly.

## 3. Component Data Flow
1. User selects a file in `DirectoryTree`.
2. `CodeBrowser` calls `WindowSwitcher.render_file(file_path)`.
3. `WindowSwitcher` determines the target window based on file type.
4. If `TextWindow` is chosen:
    - File content is loaded via `file_to_string`.
    - `text_window.load_text(content)` is called.
    - `text_window.language` is set based on extension.
    - `text_window.apply_smart_theme(current_theme)` is called.
5. `WindowSwitcher` displays `TextWindow`.

## 4. Testing Strategy
- **Unit Tests:** Verify routing logic in `WindowSwitcher`.
- **Integration Tests:** Ensure `TextWindow` correctly loads content and applies syntax highlighting based on file extension.
- **Visual Verification:** Check that Vim bindings work as expected and that themes update reactively.
