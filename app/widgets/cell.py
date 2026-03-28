from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox,
    QInputDialog, QHBoxLayout, QDialog, QListWidget, QListWidgetItem,
    QSplitter, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.interpreter import RetroInterpreter, DebugSession
import markdown2
import os
import sys
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont
import math

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


# ---------------------------------------------------------------------------
# Retro Debugger Dialog
# ---------------------------------------------------------------------------

_RETRO_DARK  = '#0d0d0d'
_RETRO_GREEN = '#33ff66'
_RETRO_YELLOW = '#ffe066'
_RETRO_PINK  = '#ff33cc'
_RETRO_FONT  = 'Courier New, monospace'

_BTN_BASE = (
    "QPushButton {{"
    "  background: #1a1a1a; color: {color}; font-family: Courier New, monospace;"
    "  font-size: 14px; border: 2px solid {color}; border-radius: 6px;"
    "  padding: 4px 14px;"
    "}}"
    "QPushButton:hover {{ background: #262626; }}"
    "QPushButton:disabled {{ color: #444; border-color: #333; }}"
)

def _btn_style(color=_RETRO_GREEN):
    return _BTN_BASE.format(color=color)


class DebuggerDialog(QDialog):
    """Retro-styled step-by-step debugger for a Retro Script code cell."""

    def __init__(self, lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RETRO DEBUGGER")
        self.setStyleSheet(
            f"background: {_RETRO_DARK}; color: {_RETRO_GREEN};"
            f"font-family: {_RETRO_FONT}; font-size: 14px;"
        )
        self.resize(860, 560)

        self._lines = lines
        self._session = DebugSession(lines)
        self._session.start()

        self._build_ui()
        self._refresh_code_view()
        self._refresh_vars()
        self._append_output_line("▶ Debug session started.  Click a line to toggle breakpoint.", _RETRO_YELLOW)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # Title bar
        title = QLabel("◈ RETRO DEBUGGER ◈")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {_RETRO_GREEN}; font-size: 18px; font-weight: bold;"
            f"font-family: {_RETRO_FONT}; letter-spacing: 4px;"
        )
        root.addWidget(title)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        self._btn_step = QPushButton("⮞ Step")
        self._btn_step.setStyleSheet(_btn_style(_RETRO_GREEN))
        self._btn_step.setToolTip("Execute the current statement and pause")
        self._btn_step.clicked.connect(self._on_step)

        self._btn_continue = QPushButton("▶ Continue")
        self._btn_continue.setStyleSheet(_btn_style(_RETRO_GREEN))
        self._btn_continue.setToolTip("Run until next breakpoint or end")
        self._btn_continue.clicked.connect(self._on_continue)

        self._btn_restart = QPushButton("↺ Restart")
        self._btn_restart.setStyleSheet(_btn_style(_RETRO_YELLOW))
        self._btn_restart.setToolTip("Restart debug session from the top")
        self._btn_restart.clicked.connect(self._on_restart)

        self._btn_stop = QPushButton("■ Stop")
        self._btn_stop.setStyleSheet(_btn_style(_RETRO_PINK))
        self._btn_stop.setToolTip("Abort debug session")
        self._btn_stop.clicked.connect(self.reject)

        for btn in [self._btn_step, self._btn_continue, self._btn_restart, self._btn_stop]:
            toolbar.addWidget(btn)
        toolbar.addStretch()

        self._lbl_status = QLabel("PAUSED")
        self._lbl_status.setStyleSheet(
            f"color: {_RETRO_YELLOW}; font-size: 13px; font-family: {_RETRO_FONT};"
        )
        toolbar.addWidget(self._lbl_status)
        root.addLayout(toolbar)

        # ── Main area: code | inspector ──────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: code listing
        code_frame = QFrame()
        code_frame.setStyleSheet(f"background: #111; border: 2px solid {_RETRO_GREEN}; border-radius: 6px;")
        code_vbox = QVBoxLayout(code_frame)
        code_vbox.setContentsMargins(4, 4, 4, 4)
        code_label = QLabel("  SOURCE  (click line to toggle breakpoint)")
        code_label.setStyleSheet(f"color: {_RETRO_YELLOW}; font-size: 12px;")
        code_vbox.addWidget(code_label)
        self._code_list = QListWidget()
        self._code_list.setStyleSheet(
            f"background: #111; color: {_RETRO_GREEN}; font-family: {_RETRO_FONT};"
            " font-size: 13px; border: none; selection-background-color: #1a2a1a;"
        )
        self._code_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._code_list.itemClicked.connect(self._on_line_clicked)
        code_vbox.addWidget(self._code_list)
        splitter.addWidget(code_frame)

        # Right: variable inspector + call stack depth
        right_frame = QFrame()
        right_frame.setStyleSheet(f"background: #111; border: 2px solid {_RETRO_GREEN}; border-radius: 6px;")
        right_vbox = QVBoxLayout(right_frame)
        right_vbox.setContentsMargins(4, 4, 4, 4)

        vars_label = QLabel("  VARIABLES")
        vars_label.setStyleSheet(f"color: {_RETRO_YELLOW}; font-size: 12px;")
        right_vbox.addWidget(vars_label)

        self._vars_list = QListWidget()
        self._vars_list.setStyleSheet(
            f"background: #111; color: {_RETRO_GREEN}; font-family: {_RETRO_FONT};"
            " font-size: 13px; border: none;"
        )
        right_vbox.addWidget(self._vars_list)

        right_vbox.addStretch()
        splitter.addWidget(right_frame)

        splitter.setSizes([520, 300])
        root.addWidget(splitter, stretch=3)

        # ── Output console ────────────────────────────────────────────────
        out_frame = QFrame()
        out_frame.setStyleSheet(f"background: #0a0a0a; border: 2px solid {_RETRO_GREEN}; border-radius: 6px;")
        out_vbox = QVBoxLayout(out_frame)
        out_vbox.setContentsMargins(4, 4, 4, 4)
        out_label = QLabel("  OUTPUT")
        out_label.setStyleSheet(f"color: {_RETRO_YELLOW}; font-size: 12px;")
        out_vbox.addWidget(out_label)
        self._output_edit = QTextEdit()
        self._output_edit.setReadOnly(True)
        self._output_edit.setStyleSheet(
            f"background: #0a0a0a; color: {_RETRO_GREEN}; font-family: {_RETRO_FONT};"
            " font-size: 13px; border: none;"
        )
        out_vbox.addWidget(self._output_edit)
        root.addWidget(out_frame, stretch=1)

    # ------------------------------------------------------------------
    # Code-view helpers
    # ------------------------------------------------------------------

    def _refresh_code_view(self):
        """Rebuild the code list with breakpoint / current-line decorations."""
        current = self._session.current_line
        breakpoints = self._session.breakpoints

        self._code_list.clear()
        for idx, raw_line in enumerate(self._lines):
            # Prefix: breakpoint marker + line number
            bp_marker = "● " if idx in breakpoints else "  "
            text = f"{bp_marker}{idx + 1:>3}  {raw_line.rstrip()}"
            item = QListWidgetItem(text)

            if idx == current and not self._session.finished:
                # Highlight current execution line
                item.setBackground(QColor('#1a3320'))
                item.setForeground(QColor(_RETRO_GREEN))
                item.setText("▶ " + text[2:])   # replace leading spaces with arrow
            elif idx in breakpoints:
                item.setForeground(QColor(_RETRO_PINK))
            else:
                item.setForeground(QColor(_RETRO_GREEN))

            self._code_list.addItem(item)

        if 0 <= current < self._code_list.count():
            self._code_list.scrollToItem(self._code_list.item(current))

    def _refresh_vars(self):
        """Rebuild the variable inspector."""
        self._vars_list.clear()
        env = self._session.interpreter.env
        if not env:
            placeholder = QListWidgetItem("(no variables yet)")
            placeholder.setForeground(QColor('#555'))
            self._vars_list.addItem(placeholder)
            return
        for name, value in sorted(env.items()):
            item = QListWidgetItem(f"  {name}  =  {value!r}")
            item.setForeground(QColor(_RETRO_GREEN))
            self._vars_list.addItem(item)

    def _append_output_line(self, text, color=None):
        color = color or _RETRO_GREEN
        self._output_edit.setTextColor(QColor(color))
        self._output_edit.append(str(text))

    def _render_state(self, state):
        """Apply a debug-state dict returned by the session to the UI."""
        event = state.get('event', '')
        outputs = state.get('output', [])

        for item in outputs:
            if isinstance(item, dict) and 'graphics' in item:
                self._append_output_line("[graphics output – run normally to view]", _RETRO_YELLOW)
            elif isinstance(item, str) and item.startswith('Error'):
                self._append_output_line(item, _RETRO_PINK)
            elif item:
                self._append_output_line(str(item))

        self._refresh_code_view()
        self._refresh_vars()

        if event == 'finished':
            self._lbl_status.setText("FINISHED")
            self._lbl_status.setStyleSheet(f"color: {_RETRO_GREEN}; font-size: 13px;")
            self._btn_step.setEnabled(False)
            self._btn_continue.setEnabled(False)
            self._append_output_line("■ Execution complete.", _RETRO_YELLOW)
        elif event == 'breakpoint':
            line_no = state.get('current_line', -1) + 1
            self._lbl_status.setText(f"BREAKPOINT  line {line_no}")
            self._lbl_status.setStyleSheet(f"color: {_RETRO_PINK}; font-size: 13px;")
            self._append_output_line(f"● Breakpoint hit at line {line_no}.", _RETRO_PINK)
        else:
            exec_line = state.get('executed_line', -1) + 1
            self._lbl_status.setText(f"PAUSED  (executed line {exec_line})")
            self._lbl_status.setStyleSheet(f"color: {_RETRO_YELLOW}; font-size: 13px;")

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_line_clicked(self, item):
        row = self._code_list.row(item)
        self._session.toggle_breakpoint(row)
        self._refresh_code_view()

    def _on_step(self):
        if self._session.finished:
            return
        state = self._session.step()
        self._render_state(state)

    def _on_continue(self):
        if self._session.finished:
            return
        state = self._session.continue_to_breakpoint()
        self._render_state(state)

    def _on_restart(self):
        self._session.start()
        self._output_edit.clear()
        self._btn_step.setEnabled(True)
        self._btn_continue.setEnabled(True)
        self._lbl_status.setText("PAUSED")
        self._lbl_status.setStyleSheet(f"color: {_RETRO_YELLOW}; font-size: 13px;")
        self._refresh_code_view()
        self._refresh_vars()
        self._append_output_line("↺ Session restarted.", _RETRO_YELLOW)


# ---------------------------------------------------------------------------
# Test Runner Dialog
# ---------------------------------------------------------------------------

class TestRunnerDialog(QDialog):
    """Retro-styled panel that runs all Test cells and shows pass/fail summary."""

    def __init__(self, cells, scroll_area, parent=None):
        super().__init__(parent)
        self.setWindowTitle("◈ RETRO TEST RUNNER ◈")
        self.setStyleSheet(
            f"background: {_RETRO_DARK}; color: {_RETRO_GREEN};"
            f"font-family: {_RETRO_FONT}; font-size: 13px;"
        )
        self.resize(760, 520)
        self._cells = cells
        self._scroll_area = scroll_area
        self._build_ui()
        self._run_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("◈ RETRO TEST RUNNER ◈")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {_RETRO_PINK}; font-size: 18px; font-weight: bold;"
            f"font-family: {_RETRO_FONT}; letter-spacing: 4px;"
        )
        root.addWidget(title)

        # Summary bar
        self._lbl_summary = QLabel("Running…")
        self._lbl_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_summary.setStyleSheet(
            f"color: {_RETRO_YELLOW}; font-size: 15px; font-family: {_RETRO_FONT};"
            f"border: 1px solid #333; padding: 4px; background: #111;"
        )
        root.addWidget(self._lbl_summary)

        # Results list
        self._result_list = QListWidget()
        self._result_list.setStyleSheet(
            f"background: #111; color: {_RETRO_GREEN};"
            f"font-family: {_RETRO_FONT}; font-size: 12px;"
            f"border: 1px solid #333;"
        )
        self._result_list.itemDoubleClicked.connect(self._jump_to_cell)
        root.addWidget(self._result_list)

        # Info label
        info = QLabel("Double-click a result to jump to that cell.")
        info.setStyleSheet(f"color: #555; font-size: 11px; font-family: {_RETRO_FONT};")
        root.addWidget(info)

        # Button row
        btn_row = QHBoxLayout()

        self._btn_rerun = QPushButton("⟳  Re-run Tests")
        self._btn_rerun.setStyleSheet(_btn_style(_RETRO_GREEN))
        self._btn_rerun.clicked.connect(self._run_all)
        btn_row.addWidget(self._btn_rerun)

        self._btn_save = QPushButton("⬇  Save Report (JSON)")
        self._btn_save.setStyleSheet(_btn_style(_RETRO_YELLOW))
        self._btn_save.clicked.connect(self._save_report)
        btn_row.addWidget(self._btn_save)

        btn_close = QPushButton("✕  Close")
        btn_close.setStyleSheet(_btn_style(_RETRO_PINK))
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Test execution
    # ------------------------------------------------------------------

    def _run_all(self):
        self._result_list.clear()
        self._lbl_summary.setText("Running…")
        self._report = []  # for optional JSON export

        test_cells = [
            (i, cell) for i, cell in enumerate(self._cells)
            if cell.cell_type.currentText() == "Test"
        ]

        if not test_cells:
            self._lbl_summary.setText("No Test cells found.")
            self._lbl_summary.setStyleSheet(
                f"color: {_RETRO_YELLOW}; font-size: 15px; font-family: {_RETRO_FONT};"
                f"border: 1px solid #333; padding: 4px; background: #111;"
            )
            return

        total_pass = 0
        total_fail = 0
        total_assert = 0

        for cell_idx, cell in test_cells:
            result = cell.run_test()
            assertions = result.get('assertions', [])
            errors = result.get('errors', [])
            n_pass = sum(1 for a in assertions if a['passed'])
            n_fail = len(assertions) - n_pass
            total_pass += n_pass
            total_fail += n_fail
            total_assert += len(assertions)

            cell_label = f"Cell {cell_idx + 1}"
            preview = cell.input.toPlainText().strip().splitlines()
            if preview:
                cell_label += f": {preview[0][:40]}"

            # Section header
            if n_fail == 0 and not errors:
                hdr_color = _RETRO_GREEN
                hdr_icon = "✓"
            else:
                hdr_color = _RETRO_PINK
                hdr_icon = "✗"

            hdr_text = (
                f"{hdr_icon} {cell_label}  "
                f"[{n_pass}/{len(assertions)} passed"
                + (f", {len(errors)} error(s)" if errors else "")
                + "]"
            )
            hdr_item = QListWidgetItem(hdr_text)
            hdr_item.setForeground(QColor(hdr_color))
            hdr_item.setData(Qt.ItemDataRole.UserRole, cell)
            self._result_list.addItem(hdr_item)

            # Per-assertion rows
            for a in assertions:
                icon = "  ✓" if a['passed'] else "  ✗"
                color = _RETRO_GREEN if a['passed'] else _RETRO_PINK
                msg = a.get('message', '')
                detail = QListWidgetItem(f"{icon} {msg}")
                detail.setForeground(QColor(color))
                detail.setData(Qt.ItemDataRole.UserRole, cell)
                self._result_list.addItem(detail)

                if not a['passed']:
                    exp = a.get('expected')
                    act = a.get('actual')
                    if exp is not None or act is not None:
                        sub = QListWidgetItem(
                            f"      expected: {exp!r}   got: {act!r}"
                        )
                        sub.setForeground(QColor(_RETRO_YELLOW))
                        sub.setData(Qt.ItemDataRole.UserRole, cell)
                        self._result_list.addItem(sub)

            # Error rows
            for e in errors:
                err_item = QListWidgetItem(f"  ⚠ {e}")
                err_item.setForeground(QColor(_RETRO_PINK))
                err_item.setData(Qt.ItemDataRole.UserRole, cell)
                self._result_list.addItem(err_item)

            # Spacer row
            spacer = QListWidgetItem("")
            spacer.setFlags(Qt.ItemFlag.NoItemFlags)
            self._result_list.addItem(spacer)

            # Build report entry
            self._report.append({
                "cell_index": cell_idx,
                "cell_preview": preview[0] if preview else "",
                "total": len(assertions),
                "passed": n_pass,
                "failed": n_fail,
                "assertions": assertions,
                "errors": errors,
            })

        # Summary
        if total_fail == 0:
            summary = f"✓  ALL PASSED  –  {total_pass}/{total_assert} assertions"
            s_color = _RETRO_GREEN
        else:
            summary = (
                f"✗  {total_fail} FAILED  –  {total_pass}/{total_assert} assertions"
            )
            s_color = _RETRO_PINK

        self._lbl_summary.setText(summary)
        self._lbl_summary.setStyleSheet(
            f"color: {s_color}; font-size: 15px; font-family: {_RETRO_FONT};"
            f"border: 1px solid #333; padding: 4px; background: #111;"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _jump_to_cell(self, item):
        cell = item.data(Qt.ItemDataRole.UserRole)
        if cell and self._scroll_area:
            self._scroll_area.ensureWidgetVisible(cell)

    def _save_report(self):
        import json
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Test Report", "test_report.json",
            "JSON Files (*.json)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._report, f, indent=2, default=str)



    def __init__(self, cell_type="Code"):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setProperty('dragged', False)  # Für visuelles Feedback

        # Drag-Handle (Griff) hinzufügen
        self.outer_layout = QHBoxLayout()
        self.drag_handle = QLabel("≡")
        self.drag_handle.setFixedWidth(24)
        self.drag_handle.setAlignment(Qt.AlignCenter)
        self.drag_handle.setStyleSheet('color: #888; font-size: 22px; padding: 0 4px;')
        self.outer_layout.addWidget(self.drag_handle)
        self.inner_layout = QVBoxLayout()

        # Zellentyp-Auswahl
        self.cell_type = QComboBox()
        self.cell_type.addItems(["Code", "Markdown", "Test"])
        self.cell_type.setCurrentText(cell_type)
        self.cell_type.currentTextChanged.connect(self._on_cell_type_changed)
        self.inner_layout.addWidget(self.cell_type)

        # Eingabe mehrzeilig
        self.input = QTextEdit()
        self.inner_layout.addWidget(self.input)

        # Ausführen-Button und Debug-Button nebeneinander
        btn_row = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.execute)
        btn_row.addWidget(self.run_button)

        self.debug_button = QPushButton("Debug")
        self.debug_button.setToolTip("Open interactive debugger for this cell")
        self.debug_button.clicked.connect(self.open_debugger)
        self.debug_button.setStyleSheet(
            f"background: #1a1a1a; color: {_RETRO_YELLOW}; font-family: {_RETRO_FONT};"
            f" font-size: 13px; border: 2px solid {_RETRO_YELLOW}; border-radius: 6px; padding: 3px 12px;"
        )
        btn_row.addWidget(self.debug_button)
        self.inner_layout.addLayout(btn_row)

        # Ausgabe (initial leer)
        self.output = QLabel("")
        self.output.setWordWrap(True)
        self.inner_layout.addWidget(self.output)

        self.outer_layout.addLayout(self.inner_layout)
        self.layout.addLayout(self.outer_layout)
        self.setLayout(self.layout)
        self.interpreter = RetroInterpreter()

        # Letztes Testergebnis (für Test-Runner-Panel)
        self.last_test_result = None

        # Soundeffekt vorbereiten
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        beep_path = resource_path("assets/beep.wav")
        self.player.setSource(f"file://{os.path.abspath(beep_path)}")
        self.audio_output.setVolume(0.25)

        # Retro-Animation: Rahmen, Scanlines, Icons
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update)
        self.anim_timer.start(60)
        self.anim_phase = 0

        # Initial styling for Test cells
        self._on_cell_type_changed(self.cell_type.currentText())

    def _on_cell_type_changed(self, cell_type):
        """Adjust UI when the cell type is switched."""
        is_test = (cell_type == "Test")
        self.debug_button.setVisible(cell_type == "Code")
        if is_test:
            self.run_button.setText("Run Tests")
            self.run_button.setStyleSheet(
                f"background: #1a1a1a; color: {_RETRO_PINK}; font-family: {_RETRO_FONT};"
                f" font-size: 13px; border: 2px solid {_RETRO_PINK}; border-radius: 6px; padding: 3px 12px;"
            )
            self.input.setPlaceholderText(
                "# Test cell – use ASSERT, ASSERT_EQ, ASSERT_APPROX\n"
                "# Example:\n"
                "LET x = 2 + 2\n"
                "ASSERT_EQ x, 4\n"
                "ASSERT x > 0\n"
                "ASSERT_APPROX 3.14159, pi, 0.001"
            )
        else:
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("")

    def open_debugger(self):
        """Open the interactive debugger for this code cell (Code cells only)."""
        if self.cell_type.currentText() != "Code":
            return
        code = self.input.toPlainText()
        lines = code.splitlines()
        if not any(line.strip() for line in lines):
            return
        dlg = DebuggerDialog(lines, parent=self)
        dlg.exec()

    def run_test(self):
        """Execute this test cell and return the result dict. Also updates the output label."""
        code = self.input.toPlainText()
        lines = code.splitlines()
        result = self.interpreter.run_test_block(lines)
        self.last_test_result = result
        self._render_test_output(result)
        return result

    def _render_test_output(self, result):
        """Render assertion pass/fail results as coloured HTML in the output label."""
        assertions = result.get('assertions', [])
        outputs = result.get('outputs', [])
        errors = result.get('errors', [])

        lines_html = []

        for a in assertions:
            if a['passed']:
                icon = '&#10003;'  # ✓
                color = _RETRO_GREEN
            else:
                icon = '&#10007;'  # ✗
                color = _RETRO_PINK
            msg = a.get('message', '')
            # Escape HTML special chars
            msg = msg.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lines_html.append(
                f"<span style='color:{color};'>{icon} {msg}</span>"
            )

        for o in outputs:
            o_esc = o.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lines_html.append(
                f"<span style='color:{_RETRO_YELLOW};'>&gt; {o_esc}</span>"
            )

        for e in errors:
            e_esc = e.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lines_html.append(
                f"<span style='color:{_RETRO_PINK};'>&#9888; {e_esc}</span>"
            )

        total = len(assertions)
        passed = sum(1 for a in assertions if a['passed'])
        failed = total - passed

        if total > 0:
            if failed == 0:
                summary_color = _RETRO_GREEN
                summary = f"&#9608; {passed}/{total} passed"
            else:
                summary_color = _RETRO_PINK
                summary = f"&#9608; {passed}/{total} passed, {failed} failed"
            lines_html.append(
                f"<span style='color:{summary_color}; font-weight:bold;'>{summary}</span>"
            )

        html = (
            f"<span style='font-family:Courier New,monospace; font-size:13px;'>"
            + "<br>".join(lines_html)
            + "</span>"
        )
        self.output.setText(html)

    def execute(self):
        # Status auf "Läuft..." setzen, falls möglich
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'set_status'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'set_status'):
            main_window.set_status('#ffff00', 'Läuft...')
        self.player.stop()  # Falls noch ein Sound läuft
        self.player.play()
        cell_type = self.cell_type.currentText()
        if cell_type == "Markdown":
            md = self.input.toPlainText()
            html = markdown2.markdown(md)
            self.output.setText(html)
            if main_window and hasattr(main_window, 'set_status'):
                main_window.set_status('#33ff66', 'Bereit')
        elif cell_type == "Test":
            result = self.run_test()
            assertions = result.get('assertions', [])
            failed = sum(1 for a in assertions if not a['passed'])
            if main_window and hasattr(main_window, 'set_status'):
                if result.get('errors') or failed:
                    main_window.set_status('#ff3333', f'Tests: {failed} failed')
                else:
                    main_window.set_status('#33ff66', 'Tests passed')
        else:
            code = self.input.toPlainText()
            lines = code.splitlines()
            results = self.interpreter.run_block(lines)
            # Ergebnisse flatten
            def flatten(items):
                for item in items:
                    if isinstance(item, list):
                        yield from flatten(item)
                    else:
                        yield item
            flat_results = list(flatten(results))
            graphics = []
            text_results = []
            error_found = False
            for result in flat_results:
                if isinstance(result, dict) and 'graphics' in result:
                    graphics.extend(result['graphics'])
                elif isinstance(result, str) and result.startswith('Error'):
                    text_results.append(result)
                    error_found = True
                elif result:
                    text_results.append(str(result))
            self.output.setText("\n".join(text_results))
            if graphics:
                self.show_graphics(graphics)
            # Status nach Ausführung setzen
            if main_window and hasattr(main_window, 'set_status'):
                if error_found:
                    main_window.set_status('#ff3333', 'Fehler beim Ausführen')
                else:
                    main_window.set_status('#33ff66', 'Bereit')

    def show_animation(self, frames):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt, QTimer
        size = 300
        dlg = QDialog(self)
        dlg.setWindowTitle("Animation")
        vbox = QVBoxLayout()
        label = QLabel()
        vbox.addWidget(label)
        dlg.setLayout(vbox)
        dlg.resize(size, size)
        pixmaps = []
        for graphics in frames:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.black)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor('#33ff66'))
            for item in graphics:
                if item['type'] == 'point':
                    x = int(item['x'] * size / 100)
                    y = int(item['y'] * size / 100)
                    painter.drawEllipse(x-2, y-2, 4, 4)
                elif item['type'] == 'line':
                    x1 = int(item['x1'] * size / 100)
                    y1 = int(item['y1'] * size / 100)
                    x2 = int(item['x2'] * size / 100)
                    y2 = int(item['y2'] * size / 100)
                    painter.drawLine(x1, y1, x2, y2)
                elif item['type'] == 'circle':
                    x = int(item['x'] * size / 100)
                    y = int(item['y'] * size / 100)
                    r = int(item['r'] * size / 100)
                    painter.drawEllipse(x - r, y - r, 2*r, 2*r)
            painter.end()
            pixmaps.append(pixmap)
        # Animation abspielen
        idx = [0]
        def next_frame():
            label.setPixmap(pixmaps[idx[0]])
            idx[0] = (idx[0] + 1) % len(pixmaps)
        timer = QTimer()
        timer.timeout.connect(next_frame)
        timer.start(300)  # 300 ms pro Frame
        dlg.exec()
        timer.stop()

    def show_graphics(self, graphics):
        # Einfache Zeichenfläche als neues Fenster
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt
        size = 300
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.black)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor('#33ff66'))
        for item in graphics:
            if item['type'] == 'point':
                x = int(item['x'] * size / 100)
                y = int(item['y'] * size / 100)
                painter.drawEllipse(x-2, y-2, 4, 4)
            elif item['type'] == 'line':
                x1 = int(item['x1'] * size / 100)
                y1 = int(item['y1'] * size / 100)
                x2 = int(item['x2'] * size / 100)
                y2 = int(item['y2'] * size / 100)
                painter.drawLine(x1, y1, x2, y2)
            elif item['type'] == 'circle':
                x = int(item['x'] * size / 100)
                y = int(item['y'] * size / 100)
                r = int(item['r'] * size / 100)
                painter.drawEllipse(x - r, y - r, 2*r, 2*r)
        painter.end()
        dlg = QDialog(self)
        dlg.setWindowTitle("Grafik")
        vbox = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        vbox.addWidget(label)
        dlg.setLayout(vbox)
        dlg.exec()

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Glow-Rahmen
        for i in range(1, 4):
            qp.setPen(QPen(QColor(51,255,102, 18//i), 6+2*i))
            qp.drawRoundedRect(2-i, 2-i, w-4+2*i, h-4+2*i, 12+i, 12+i)
        qp.setPen(QPen(QColor('#33ff66'), 2))
        qp.drawRoundedRect(2, 2, w-4, h-4, 12, 12)
        # Scanlines
        for y in range(8, h-8, 4):
            y_off = y + (self.anim_phase % 8)
            color = QColor(30,30,30,60)
            if y%16==0:
                color = QColor('#33ff66') if (y//16)%2==0 else QColor('#ffe066')
                color.setAlpha(40)
            qp.setPen(QPen(color, 1))
            qp.drawLine(8, y_off, w-8, y_off)
        # CRT-Vignette (korrekt mit QLinearGradient)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(0,0,0,80))
        grad.setColorAt(0.5, QColor(0,0,0,0))
        grad.setColorAt(1, QColor(0,0,0,80))
        qp.setBrush(grad)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.drawRoundedRect(2, 2, w-4, h-4, 12, 12)
        # Disketten-Icon (unten rechts)
        t = self.anim_phase
        dx = int(w-36+math.sin(t/11)*2)
        dy = int(h-36+math.cos(t/13)*2)
        qp.setBrush(QColor('#33ff66'))
        qp.setPen(QPen(QColor('#222'), 2))
        qp.drawRect(dx, dy, 18, 18)
        qp.setBrush(QColor('#ffe066'))
        qp.drawRect(dx+6, dy+9, 6, 6)
        # Cursor-Icon (oben links, blinkt)
        if (self.anim_phase//10)%2 == 0:
            qp.setPen(QPen(QColor('#ff33cc'), 2))
            qp.drawLine(12, 12, 22, 22)
            qp.drawLine(22, 22, 18, 22)
            qp.drawLine(22, 22, 22, 18)
        self.anim_phase += 1
        qp.end()