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


class NotebookCell(QWidget):
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
        self.cell_type.addItems(["Code", "Markdown"])
        self.cell_type.setCurrentText(cell_type)
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
        self.inner_layout.addWidget(self.output)

        self.outer_layout.addLayout(self.inner_layout)
        self.layout.addLayout(self.outer_layout)
        self.setLayout(self.layout)
        self.interpreter = RetroInterpreter()

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

    def execute(self):
        # Status auf "Läuft..." setzen, falls möglich
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'set_status'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'set_status'):
            main_window.set_status('#ffff00', 'Läuft...')
        self.player.stop()  # Falls noch ein Sound läuft
        self.player.play()
        if self.cell_type.currentText() == "Markdown":
            md = self.input.toPlainText()
            html = markdown2.markdown(md)
            self.output.setText(html)
            if main_window and hasattr(main_window, 'set_status'):
                main_window.set_status('#33ff66', 'Bereit')
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