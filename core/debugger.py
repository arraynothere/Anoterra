"""IDE side of the Python debugger (Qt signals, no widgets).

``DebugSession`` starts ``core/debug_worker.py`` in a child process (through
``CodeRunnerEngine`` so output, input, Stop and timeout behave like a normal run) and
talks to it over a local socket. See ``debug_worker`` for the protocol.
"""
import json
import os
import secrets
import socket
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from core.languages import RunError, RunPlan, find_python
from core.runner import CodeRunnerEngine

PYTHON_EXTENSIONS = (".py", ".pyw")
CONNECT_TIMEOUT = 20


def worker_path():
    """Location of debug_worker.py (also inside a PyInstaller bundle)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "core", "debug_worker.py")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_worker.py")


def can_debug(file_path):
    return bool(file_path) and os.path.splitext(file_path)[1].lower() in PYTHON_EXTENSIONS


class _DebugRunner(CodeRunnerEngine):
    """Runs the debug worker instead of the script itself."""

    def __init__(self, file_path, port, token, **kwargs):
        super().__init__(file_path, run_mode="run", **kwargs)
        self.port = port
        self.token = token

    def start(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.error_signal.emit("[Error] File not found or not saved yet.\n")
            self.finished_signal.emit(-1, {})
            return
        try:
            python = find_python(self.python_exe)
        except RunError as exc:
            self.error_signal.emit(f"[Error] {exc}\n")
            self.finished_signal.emit(-1, {})
            return
        command = [python, "-u", worker_path(), str(self.port), self.token, self.file_path] + self.args
        self._is_running = True
        threading.Thread(target=self._execute, args=(RunPlan(run=command, label="Python (debug)"),),
                         daemon=True).start()


class DebugSession(QObject):
    """One debugging session. ``paused`` carries the worker's message (reason + call stack)."""

    paused = pyqtSignal(dict)
    resumed = pyqtSignal()
    connection_failed = pyqtSignal(str)

    def __init__(self, file_path, breakpoints, stop_on_entry=False, args=None, timeout=0,
                 python_exe=None, parent=None):
        super().__init__(parent)
        self.breakpoints = breakpoints
        self.stop_on_entry = stop_on_entry
        self._token = secrets.token_hex(16)
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(1)
        self._server.settimeout(CONNECT_TIMEOUT)
        self._conn = None
        self._send_lock = threading.Lock()
        self._closed = False
        self.is_paused = False
        self.runner = _DebugRunner(file_path, self._server.getsockname()[1], self._token,
                                   args=args, timeout=timeout, python_exe=python_exe, parent=self)

    def start(self):
        threading.Thread(target=self._serve, daemon=True).start()
        self.runner.start()

    def close(self):
        self._closed = True
        for sock in (self._conn, self._server):
            try:
                if sock is not None:
                    sock.close()
            except OSError:
                pass

    # ---- commands --------------------------------------------------------------------------
    def resume(self, kind, breakpoints=None):
        """kind: continue | step | next | out"""
        if not self.is_paused:
            return
        if breakpoints is not None:
            self.set_breakpoints(breakpoints)
        self.is_paused = False
        self._send({"cmd": kind})
        self.resumed.emit()

    def set_breakpoints(self, breakpoints):
        self.breakpoints = breakpoints
        self._send({"cmd": "breakpoints", "files": breakpoints})

    def _send(self, message):
        conn = self._conn
        if conn is None:
            return
        data = (json.dumps(message) + "\n").encode("utf-8")
        try:
            with self._send_lock:
                conn.sendall(data)
        except OSError:
            pass

    # ---- worker thread ---------------------------------------------------------------------
    def _serve(self):
        try:
            conn, _ = self._server.accept()
        except OSError:
            if not self._closed and not self.runner.is_running:
                return
            if not self._closed:
                self.connection_failed.emit("The debugger process did not connect back to Anoterra.")
            return
        self._conn = conn
        try:
            conn.settimeout(None)
            reader = conn.makefile("r", encoding="utf-8", newline="\n")
            hello = json.loads(reader.readline() or "{}")
            if hello.get("token") != self._token:
                conn.close()
                self.connection_failed.emit("Rejected a debugger connection with a wrong token.")
                return
            self._send({"cmd": "start", "breakpoints": self.breakpoints, "entry": self.stop_on_entry})
            for line in reader:
                line = line.strip()
                if not line:
                    continue
                message = json.loads(line)
                if message.get("event") == "paused":
                    self.is_paused = True
                    self.paused.emit(message)
        except (OSError, ValueError):
            pass
