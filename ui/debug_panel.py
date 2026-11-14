"""Debugger UI: the Debug tab (variables, call stack, step buttons) and the controller that
connects it to the editors, the output view and ``core.debugger.DebugSession``."""
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QSplitter, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.debugger import DebugSession, can_debug
from core.editor import AnoterraEditor

IDLE_TEXT = "No active debug session. Press F9 to set breakpoints, Ctrl+Shift+F5 to start."


class DebugPanel(QWidget):
    """Buttons + variables + call stack. Emits requests; knows nothing about the session."""

    action_requested = pyqtSignal(str)       # continue | step | next | out | stop
    frame_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)
        self.status = QLabel(IDLE_TEXT)
        header.addWidget(self.status, 1)
        self.buttons = {}
        for key, text, tip in (
            ("continue", "Continue", "Continue (F8)"),
            ("next", "Step Over", "Step over (F10)"),
            ("step", "Step Into", "Step into (F11)"),
            ("out", "Step Out", "Step out (Shift+F11)"),
            ("stop", "Stop", "Stop debugging (Shift+F5)"),
        ):
            button = QPushButton(text)
            button.setProperty("secondary", True)
            button.setToolTip(tip)
            button.clicked.connect(lambda _checked=False, k=key: self.action_requested.emit(k))
            header.addWidget(button)
            self.buttons[key] = button
        layout.addLayout(header)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.variables = QTreeWidget()
        self.variables.setHeaderLabels(["Variable", "Type", "Value"])
        self.variables.setRootIsDecorated(False)
        self.variables.setColumnWidth(0, 160)
        self.variables.setColumnWidth(1, 90)
        self.stack = QListWidget()
        self.stack.currentRowChanged.connect(self._on_row_changed)
        split.addWidget(self.variables)
        split.addWidget(self.stack)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)
        self.reset()

    def _on_row_changed(self, row):
        if row >= 0:
            self.frame_selected.emit(row)

    def _enable(self, paused, active):
        for key in ("continue", "next", "step", "out"):
            self.buttons[key].setEnabled(paused)
        self.buttons["stop"].setEnabled(active)

    def reset(self):
        self.status.setText(IDLE_TEXT)
        self.variables.clear()
        self.stack.blockSignals(True)
        self.stack.clear()
        self.stack.blockSignals(False)
        self._enable(False, False)

    def set_running(self, text="Running..."):
        self.status.setText(text)
        self.variables.clear()
        self.stack.blockSignals(True)
        self.stack.clear()
        self.stack.blockSignals(False)
        self._enable(False, True)

    def set_paused(self, text, frames):
        self.status.setText(text)
        self.stack.blockSignals(True)
        self.stack.clear()
        for frame in frames:
            self.stack.addItem(f"{frame['name']}   {os.path.basename(frame['file'])}:{frame['line']}")
        self.stack.setCurrentRow(0)
        self.stack.blockSignals(False)
        self._enable(True, True)
        self.show_variables(frames[0]["vars"] if frames else [])

    def show_variables(self, variables):
        self.variables.clear()
        for name, type_name, value in variables:
            item = QTreeWidgetItem([name, type_name, value])
            item.setToolTip(2, value)
            self.variables.addTopLevelItem(item)


class DebugController:
    """Owns the session and keeps editors, output view and panel in sync."""

    def __init__(self, window):
        self.window = window
        self.session = None
        self.frames = []
        self._tab_shown = False
        self.panel = DebugPanel()
        self.panel.action_requested.connect(self._on_action)
        self.panel.frame_selected.connect(self._on_frame_selected)

    # ---- breakpoints -----------------------------------------------------------------------
    def collect_breakpoints(self):
        files = {}
        for editor in self.window._editors():
            if editor.file_path:
                lines = [line + 1 for line in editor.breakpoint_lines()]
                if lines:
                    files[os.path.abspath(editor.file_path)] = lines
        return files

    def toggle_breakpoint(self):
        editor = self.window.current_editor()
        if editor is None:
            return
        editor.toggle_breakpoint()
        self._push_breakpoints()

    def clear_breakpoints(self):
        for editor in self.window._editors():
            editor.clear_breakpoints()
        self._push_breakpoints()

    def _push_breakpoints(self):
        if self.session is not None:
            self.session.set_breakpoints(self.collect_breakpoints())

    # ---- session ---------------------------------------------------------------------------
    def start(self):
        window = self.window
        editor = window.current_editor()
        if editor is None:
            return
        if not editor.file_path:
            window._save_editor(editor)
            if not editor.file_path:
                return
        elif window.prefs["save_before_run"] and editor.is_modified_flag:
            window._save_editor(editor)
        if not can_debug(editor.file_path):
            QMessageBox.information(window, "Debugger", "The debugger supports Python files (.py) only.")
            return

        window._stop_execution(silent=True)
        self._end_session()
        breakpoints = self.collect_breakpoints()
        view = window.output_page.view
        view.clear()
        window._show_bottom(0)
        path = editor.file_path
        args = window.run_args.get(path, [])
        view.append_text(f"[DEBUG] {path}" + (f"  {' '.join(args)}" if args else "") + "\n", "info")
        if not breakpoints:
            view.append_text("[Debug] No breakpoints set - stopping on the first line.\n", "info")

        self._tab_shown = False
        self.session = session = DebugSession(
            path, breakpoints, stop_on_entry=not breakpoints, args=args,
            timeout=window.prefs["run_timeout"], python_exe=window.prefs["python_path"] or None, parent=window)
        runner = session.runner
        window.active_runner = runner
        runner.output_signal.connect(lambda text: view.append_text(text, "out"))
        runner.error_signal.connect(lambda text: view.append_text(text, "err"))
        runner.finished_signal.connect(
            lambda code, metrics, r=runner: self._on_finished(code, metrics, r))
        session.paused.connect(self._on_paused)
        session.connection_failed.connect(lambda text: view.append_text(f"[Debug] {text}\n", "err"))
        window.output_page.set_running(True, f"Debugging {os.path.basename(path)}...")
        self.panel.set_running("Running to the first breakpoint...")
        session.start()

    def _end_session(self):
        if self.session is not None:
            self.session.close()
            self.session = None
        self.frames = []
        self._clear_markers()
        self.panel.reset()

    def _on_finished(self, code, metrics, runner):
        if self.session is None or runner is not self.session.runner:
            return
        self.window._on_execution_finished(code, metrics, runner)
        self._end_session()

    def _on_paused(self, info):
        self.frames = [f for f in info.get("stack", []) if f.get("file")]
        if not self.frames:
            return
        reason = {"breakpoint": "Paused on breakpoint", "return": "Returning from function"}.get(
            info.get("reason"), "Paused")
        top = self.frames[0]
        text = f"{reason} - {top['name']} ({os.path.basename(top['file'])}:{top['line']})"
        if info.get("return_value") is not None:
            text += f"  returns {info['return_value']}"
        self.panel.set_paused(text, self.frames)
        if not self._tab_shown:
            self._tab_shown = True
            self.window.output_panel.show()
            self.window.bottom_tabs.setCurrentWidget(self.panel)
        self._show_frame(0)
        self.window.raise_()
        self.window.activateWindow()

    def _on_frame_selected(self, row):
        if 0 <= row < len(self.frames):
            self.panel.show_variables(self.frames[row]["vars"])
            self._show_frame(row)

    def _show_frame(self, row):
        frame = self.frames[row]
        self._clear_markers()
        if not os.path.isfile(frame["file"]):
            return
        editor = self.window._open_path(frame["file"], frame["line"])
        if isinstance(editor, AnoterraEditor):
            editor.set_debug_line(frame["line"] - 1)
            editor.go_to_line(frame["line"])

    def _clear_markers(self):
        for editor in self.window._editors():
            editor.set_debug_line(None)

    # ---- user actions ----------------------------------------------------------------------
    def action(self, kind):
        self._on_action(kind)

    def _on_action(self, kind):
        if kind == "stop":
            self.window._stop_execution()
            return
        session = self.session
        if session is None or not session.is_paused:
            return
        self._clear_markers()
        self.panel.set_running("Running...")
        session.resume(kind, self.collect_breakpoints())
