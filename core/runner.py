import codecs
import os
import shutil
import subprocess
import threading
import time

import psutil
from PyQt6.QtCore import QObject, pyqtSignal

from core.languages import RunError, run_plan

class CodeRunnerEngine(QObject):
    """Runs a source file in a child process and streams its output.

    Signals are emitted from worker threads; Qt delivers them to the GUI thread.
    ``finished_signal`` carries (exit_code, metrics). ``metrics['duration']`` is
    always present; debug mode adds cpu_percent / peak_cpu_percent / memory_mb / threads.
    """

    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, dict)

    def __init__(self, file_path, run_mode="run", args=None, timeout=0, python_exe=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.run_mode = run_mode
        self.args = list(args or [])
        self.timeout = timeout
        self.python_exe = python_exe
        self.process = None
        self._is_running = False
        self._stopped = False
        self._timed_out = False

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.error_signal.emit("[Error] File not found or not saved yet.\n")
            self.finished_signal.emit(-1, {})
            return
        try:
            plan = run_plan(self.file_path, self.python_exe, self.run_mode == "debug", self.args)
        except RunError as exc:
            self.error_signal.emit(f"[Error] {exc}\n")
            self.finished_signal.emit(-1, {})
            return
        self._is_running = True
        threading.Thread(target=self._execute, args=(plan,), daemon=True).start()

    def send_input(self, text):
        process = self.process
        if not process or process.poll() is not None or process.stdin is None:
            return False
        try:
            process.stdin.write((text + "\n").encode("utf-8"))
            process.stdin.flush()
            return True
        except (OSError, ValueError):
            return False

    def stop(self):
        self._stopped = True
        process = self.process
        if process and process.poll() is None:
            self._kill_tree(process.pid, force=False)
            threading.Timer(2.0, self._force_kill).start()

    def _force_kill(self):
        process = self.process
        if process and process.poll() is None:
            self._kill_tree(process.pid, force=True)

    @staticmethod
    def _kill_tree(pid, force):
        try:
            parent = psutil.Process(pid)
        except psutil.Error:
            return
        targets = []
        try:
            targets = parent.children(recursive=True)
        except psutil.Error:
            pass
        targets.append(parent)
        for proc in targets:
            try:
                proc.kill() if force else proc.terminate()
            except psutil.Error:
                pass

    def _execute(self, plan):
        started = time.perf_counter()
        cwd = os.path.dirname(os.path.abspath(self.file_path))
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        exit_code = -99
        metrics = {}
        try:
            for step in plan.steps:
                if self.run_mode == "debug":
                    self.output_signal.emit(f"[Build] {' '.join(step)}\n")
                result = subprocess.run(step, cwd=cwd, capture_output=True, text=True,
                                        errors="replace", creationflags=flags)
                if result.stdout:
                    self.output_signal.emit(result.stdout)
                if result.returncode != 0:
                    self.error_signal.emit(f"[Compilation Error]\n{result.stderr}")
                    exit_code = result.returncode
                    return
                if result.stderr:
                    self.error_signal.emit(result.stderr)

            env = os.environ.copy()
            env.update({"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
            if self.run_mode == "debug":
                env["PYTHONFAULTHANDLER"] = "1"
            self.process = subprocess.Popen(
                plan.run, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0, creationflags=flags,
            )
            sampler = _ResourceSampler(self.process.pid) if self.run_mode == "debug" else None
            readers = [
                threading.Thread(target=self._pump, args=(self.process.stdout, self.output_signal), daemon=True),
                threading.Thread(target=self._pump, args=(self.process.stderr, self.error_signal), daemon=True),
            ]
            for reader in readers:
                reader.start()
            if sampler:
                sampler.start()

            try:
                self.process.wait(timeout=self.timeout if self.timeout and self.timeout > 0 else None)
            except subprocess.TimeoutExpired:
                self._timed_out = True
                self._kill_tree(self.process.pid, force=True)
                self.process.wait()

            for reader in readers:
                reader.join(timeout=2.0)
            exit_code = self.process.returncode
            if sampler:
                sampler.stop()
                metrics.update(sampler.summary())
        except Exception as exc:  # noqa: BLE001 - surface any launch failure in the console
            self.error_signal.emit(f"[Execution Exception] {exc}\n")
            exit_code = -99
        finally:
            metrics["duration"] = time.perf_counter() - started
            metrics["stopped"] = self._stopped
            metrics["timed_out"] = self._timed_out
            if plan.cleanup_dir:
                shutil.rmtree(plan.cleanup_dir, ignore_errors=True)
            self._is_running = False
            self.finished_signal.emit(exit_code if exit_code is not None else -1, metrics)

    @staticmethod
    def _pump(stream, signal):
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                text = decoder.decode(chunk)
                if text:
                    signal.emit(text)
            tail = decoder.decode(b"", final=True)
            if tail:
                signal.emit(tail)
        except (OSError, ValueError):
            pass

class _ResourceSampler(threading.Thread):
    """Polls CPU / memory / thread usage of a process tree (debug mode)."""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid = pid
        self._halt = threading.Event()
        self.cpu_samples = []
        self.peak_cpu = 0.0
        self.peak_memory = 0.0
        self.peak_threads = 0

    def run(self):
        try:
            root = psutil.Process(self.pid)
        except psutil.Error:
            return
        known = {}
        while not self._halt.is_set():
            try:
                procs = [root] + root.children(recursive=True)
                cpu = memory = threads = 0
                for proc in procs:
                    cached = known.setdefault(proc.pid, proc)
                    cpu += cached.cpu_percent(interval=None)
                    memory += cached.memory_info().rss
                    threads += cached.num_threads()
                self.cpu_samples.append(cpu)
                self.peak_cpu = max(self.peak_cpu, cpu)
                self.peak_memory = max(self.peak_memory, memory / (1024 * 1024))
                self.peak_threads = max(self.peak_threads, threads)
            except psutil.Error:
                pass
            self._halt.wait(0.1)

    def stop(self):
        self._halt.set()
        self.join(timeout=1.0)

    def summary(self):
        average = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        return {
            "cpu_percent": round(average, 1),
            "peak_cpu_percent": round(self.peak_cpu, 1),
            "memory_mb": self.peak_memory,
            "threads": self.peak_threads,
        }
