# Design Spec: TextWindow Integration with TextArea

- **Date:** 2026-03-24
- **Topic:** Replacing StaticWindow with TextArea for code/text files in Browsr

## 1. Goal
Introduce a new `TextWindow` widget based on Textual's [TextArea](https://textual.textualize.io/widgets/text_area/) to provide a higher-performance, editor-like experience for viewing code and text files, while maintaining `StaticWindow` for specialized Rich rendering (Markdown, Images, Exceptions).

## 2. Research & Resources

### 2.1 Technical Documentation
- **Textual TextArea Documentation:** [https://textual.textualize.io/widgets/text_area/](https://textual.textualize.io/widgets/text_area/)
- **Syntax Engine:** Unlike other Textual widgets that use Pygments, `TextArea` is powered by **tree-sitter** for incremental parsing and high-performance highlighting.
- **Dependencies:** Requires `textual[syntax]` which installs `tree-sitter` and `tree-sitter-languages`.

### 2.2 Key Findings from Discovery
- **Built-in Themes:** `TextArea` includes themes such as `monokai`, `dracula`, `github_light`, and `vscode_dark`. These are accessible via the `available_themes` property.
- **Language Support:** Supported languages (e.g., `python`, `javascript`, `json`, `sql`) can be queried via `available_languages`.
- **Reactive Attributes:** Both `language` and `theme` are reactive, allowing for instant UI updates when changed.
- **Vim Bindings:** Native cursor actions (`cursor_up`, `cursor_down`, etc.) can be mapped directly to key bindings, bypassing the need for external scroll wrappers.

## 3. Architecture

### 3.1 The `TextWindow` Widget
- **Inheritance:** `class TextWindow(TextArea, BaseCodeWindow)`
- **Configuration:** Initialized as `read_only=True` and `soft_wrap=False`.
- **Vim Bindings:** Native Vim navigation bindings (`h`, `j`, `k`, `l`) added directly to the `BINDINGS` list, mapping to `TextArea`'s internal cursor actions (`cursor_left`, `cursor_down`, `cursor_up`, `cursor_right`).
- **Scrolling:** Leverages `TextArea`'s built-in high-performance scrolling.

### 3.2 WindowSwitcher Routing Logic
The `WindowSwitcher` will be updated to route files as follows:

- **DataTableWindow:** `.csv`, `.parquet`, `.feather`
- **StaticWindow:**
    - Markdown (`.md`)
    - Images
    - Exceptions/Errors (using Rich ASCII art)
- **TextWindow (NEW):**
    - JSON (`.json`)
    - All other code files (Python, JS, etc.)
    - Generic text files

### 3.3 Syntax & Theme Intelligence
- **Syntax Detection:** Map file extensions to `TextArea.available_languages` (tree-sitter names).
- **Theme Mapping:** Map Browsr's Rich-based themes to the closest `TextArea.available_themes` equivalents.
    - Example: `monokai` -> `monokai`, `dracula` -> `dracula`, `github-dark` -> `vscode_dark`, `solarized-light` -> `github_light`.
- **Reactive Updates:** `TextWindow` will watch the global application theme and update its internal `theme` attribute accordingly.

## 4. Component Data Flow
1. User selects a file in `DirectoryTree`.
2. `CodeBrowser` calls `WindowSwitcher.render_file(file_path)`.
3. `WindowSwitcher` determines the target window based on file type.
4. If `TextWindow` is chosen:
    - File content is loaded via `file_to_string`.
    - `text_window.load_text(content)` is called.
    - `text_window.language` is set based on extension.
    - `text_window.apply_smart_theme(current_theme)` is called.
5. `WindowSwitcher` displays `TextWindow`.

## 5. Testing Strategy
- **Unit Tests:** Verify routing logic in `WindowSwitcher`.
- **Integration Tests:** Ensure `TextWindow` correctly loads content and applies syntax highlighting based on file extension.
- **Visual Verification:** Check that Vim bindings work as expected and that themes update reactively.
