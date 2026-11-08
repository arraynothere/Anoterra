import subprocess
import threading
import sys
import os
import psutil
from PyQt6.QtCore import QObject, pyqtSignal

class CodeRunnerEngine(QObject):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, dict)

    def __init__(self, file_path, run_mode="run"):
        super().__init__()
        self.file_path = file_path
        self.run_mode = run_mode
        self.process = None
        self._is_running = False

    def start(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.output_signal.emit("[Error] File not found or not saved yet.\n")
            self.finished_signal.emit(-1, {})
            return

        self._is_running = True
        threading.Thread(target=self._execute_process, daemon=True).start()

    def _execute_process(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        cmd = []

        if ext in ['.py', '.pyw']:
            cmd = [sys.executable, self.file_path]
        elif ext in ['.js']:
            cmd = ["node", self.file_path]
        elif ext in ['.cpp', '.cc']:
            output_bin = self.file_path + (".exe" if os.name == "nt" else "")
            compile_res = subprocess.run(["g++", self.file_path, "-o", output_bin], capture_output=True, text=True)
            if compile_res.returncode != 0:
                self.output_signal.emit(f"[Compilation Error]\n{compile_res.stderr}")
                self.finished_signal.emit(compile_res.returncode, {})
                return
            cmd = [output_bin]
        else:
            self.output_signal.emit(f"[Error] Unsupported execution extension: {ext}\n")
            self.finished_signal.emit(-1, {})
            return

        if self.run_mode == "debug":
            self.output_signal.emit(f"[Debugger] Initializing profiling session for: {os.path.basename(self.file_path)}\n")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            pid = self.process.pid
            p_obj = psutil.Process(pid)

            while self.process.poll() is None:
                if not self._is_running:
                    self.process.terminate()
                    break
                try:
                    stdout_data = self.process.stdout.readline()
                    if stdout_data:
                        self.output_signal.emit(stdout_data)
                except Exception:
                    break

            stdout, stderr = self.process.communicate()
            if stdout:
                self.output_signal.emit(stdout)
            if stderr:
                self.output_signal.emit(stderr)

            exit_code = self.process.returncode
            metrics = {}
            if self.run_mode == "debug":
                try:
                    metrics = {
                        "cpu_percent": p_obj.cpu_percent(interval=0.1),
                        "memory_mb": p_obj.memory_info().rss / (1024 * 1024),
                        "threads": p_obj.num_threads()
                    }
                except Exception:
                    pass

            self.output_signal.emit(f"\n[Process exited with code {exit_code}]\n")
            self.finished_signal.emit(exit_code, metrics)

        except Exception as e:
            self.output_signal.emit(f"[Execution Exception] {str(e)}\n")
            self.finished_signal.emit(-99, {})

    def stop(self):
        self._is_running = False
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
