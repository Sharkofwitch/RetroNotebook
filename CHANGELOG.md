# Changelog

All notable changes to **Retro Notebook** are documented here.

---

## [1.3.0] – 2025 (Cell Assertions & Test Runner)

### Added
- **Test cell type** – new `Test` option in the cell-type selector.  
  Test cells use the Retro Script interpreter in a fresh, sandboxed context so
  they cannot affect game/progress systems.
- **Three assertion styles** supported in Test cells:
  - `ASSERT expr` – passes when *expr* is truthy
  - `ASSERT_EQ a, b` – passes when `a == b`
  - `ASSERT_APPROX a, b [, tol]` – passes when `|a - b| ≤ tol` (default `1e-6`)
- **Per-cell run** – "Run Tests" button (replacing the standard "Run" button for
  Test cells) executes the cell and renders colour-coded ✓/✗ results inline.
- **Test Runner panel** (`▶  Run Tests` button in the main toolbar) – opens a
  retro-styled dialog that:
  - Runs every Test cell in the notebook in one go
  - Shows total / pass / fail counts in a summary bar
  - Lists per-cell and per-assertion details
  - Highlights failed assertions with expected vs. actual values
  - Lets you double-click any result row to jump to that cell
  - Offers an optional **Save Report (JSON)** export
- **Test results are not persisted** as notebook content; only the source code
  of a Test cell is saved (the output panel is cleared on load).
- Updated `HELP` command output to document the new assertion commands.
- Placeholder text in Test cells shows usage examples.

### Changed
- `NotebookCell` combo box now includes "Code", "Markdown", **and "Test"**.
- About dialog updated to v1.3.
- `storage.py` – Test cell outputs are intentionally excluded from saves.

---

## [1.2.0] – 2025 (Interactive Debugger)

### Added
- **Interactive step-by-step debugger** (`Debug` button on Code cells).
  - Line-by-line execution with a highlighted source view.
  - Variable inspector updated after every step.
  - Breakpoint support: click any source line to toggle a breakpoint, then use
    "Continue" to run to the next breakpoint.
  - Restart session without closing the dialog.
- `DebugSession` class in `interpreter.py` that drives the debugger; groups
  source lines into logical steps (handles IF/WHILE/FOR blocks as single steps).

---

## [1.1.0] – 2025 (CodeGrid & Bit Factory)

### Added
- **CodeGrid** minigame – logic puzzle with multiple modes, Daily Challenge,
  XP, Highscore, Achievements, and a seed system.
- **Bit Factory** minigame – survival builder.
- Animated, atmospheric start screen and menus.
- About dialog in retro style.
- Drag & Drop for notebook cells.
- Mac-compatible resource handling (`resource_path`) for app bundles.

---

## [1.0.0] – 2025 (Initial Release)

### Added
- Retro-inspired desktop notebook with CRT look, scanlines, glow, animated
  pixels and retro icons.
- Code cells with a custom interpreter supporting:
  - Variables and lists (`LET`)
  - Strings with index assignment
  - Conditions (`IF / ELSE / ENDIF`)
  - Loops (`WHILE / ENDWHILE`, `FOR / NEXT`)
  - Functions (`DEF`)
  - Graphics commands (`POINT`, `LINE`, `CIRCLE`)
  - Animation frames (`FRAME / ENDFRAME`)
  - Built-in functions: `len`, `str`, `int`, `float`, `list`, `ord`, `chr`,
    `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`
  - Constants: `pi`, `π`, `e`
  - `INPUT` command (GUI dialog)
  - `HELP` command
- Markdown cells rendered with `markdown2`.
- Sound effects on cell execution and startup.
- Save / Load notebooks (JSON).
- Endless-loop protection (max 1000 WHILE iterations).
- Error catching with descriptive messages.
- XP, Highscore, and Achievement system.
- Daily Challenge mode.
