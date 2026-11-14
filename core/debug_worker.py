"""Debug worker: runs a Python script under ``bdb`` and talks to the Anoterra IDE.

This file is started as a *separate process* by ``core.debugger`` and uses the standard
library only, so it works with any Python 3.8+ interpreter (including the one in a venv).

Protocol: JSON lines over a local TCP socket (127.0.0.1, random port, secret token).
  worker -> IDE   {"event": "paused", "reason": str, "stack": [frame, ...]}
  IDE -> worker   {"cmd": "start", "breakpoints": {...}, "entry": bool}   (first message)
                  {"cmd": "continue" | "step" | "next" | "out"}
                  {"cmd": "breakpoints", "files": {path: [line, ...]}}
"""
import bdb
import json
import os
import queue
import socket
import sys
import threading
import types

MAX_VARS = 80
MAX_REPR = 200
_HIDDEN_TYPES = (types.ModuleType, types.FunctionType, types.BuiltinFunctionType, types.MethodType, type)


def _safe_repr(value):
    try:
        text = repr(value)
    except Exception as exc:  # noqa: BLE001 - user __repr__ may raise anything
        text = f"<repr failed: {exc.__class__.__name__}>"
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    return text if len(text) <= MAX_REPR else text[:MAX_REPR] + "..."


def _frame_variables(frame):
    result = []
    for name, value in list(frame.f_locals.items()):
        if name.startswith("__") or isinstance(value, _HIDDEN_TYPES):
            continue
        result.append([str(name), type(value).__name__, _safe_repr(value)])
        if len(result) >= MAX_VARS:
            break
    return result


class Connection:
    def __init__(self, port, token):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        self.sock.settimeout(None)
        self._lock = threading.Lock()
        self._file = self.sock.makefile("r", encoding="utf-8", newline="\n")
        self.send({"event": "hello", "token": token, "pid": os.getpid()})

    def send(self, message):
        data = (json.dumps(message) + "\n").encode("utf-8")
        with self._lock:
            self.sock.sendall(data)

    def messages(self):
        for line in self._file:
            line = line.strip()
            if line:
                yield json.loads(line)


class IdeDebugger(bdb.Bdb):
    def __init__(self, connection, script):
        super().__init__(skip=["importlib*", "bdb", "runpy", "threading"])
        self.connection = connection
        self.script = os.path.abspath(script)
        self._commands = queue.Queue()
        self._wanted = {}
        self._out_frame = None
        self._internal = {self._key(bdb.__file__), self._key(__file__)}

    # ---- IDE -> worker -------------------------------------------------------------------
    def listen(self):
        try:
            for message in self.connection.messages():
                cmd = message.get("cmd")
                if cmd == "breakpoints":
                    self.apply_breakpoints(message.get("files", {}))
                elif cmd in ("continue", "step", "next", "out"):
                    self._commands.put(cmd)
        except (OSError, ValueError):
            pass
        os._exit(1)  # IDE closed the connection: never leave an orphaned process behind

    def apply_breakpoints(self, files):
        wanted = {}
        for path, lines in files.items():
            wanted[self.canonic(path)] = (path, {int(n) for n in lines})
        for canon, (path, lines) in wanted.items():
            current = set(self.get_file_breaks(path))
            for line in current - lines:
                self.clear_break(path, line)
            for line in lines - current:
                self.set_break(path, line)
        for canon, (path, lines) in self._wanted.items():
            if canon not in wanted:
                self.clear_all_file_breaks(path)
        self._wanted = wanted

    # ---- bdb hooks -----------------------------------------------------------------------
    def user_line(self, frame):
        canon = self.canonic(frame.f_code.co_filename)
        hit = frame.f_lineno in self.breaks.get(canon, ())
        self._pause(frame, "breakpoint" if hit else "step")

    def user_return(self, frame, return_value):
        if frame is self._out_frame:      # "Step Out": land in the caller instead of pausing on the return
            self._out_frame = None
            self.set_step()
            return
        self._pause(frame, "return", return_value)

    @staticmethod
    def _key(filename):
        return os.path.normcase(os.path.splitext(os.path.abspath(filename))[0])

    def _is_internal(self, frame):
        return self._key(frame.f_code.co_filename) in self._internal

    def run_code(self, code, namespace, stop_on_entry):
        """Like ``Bdb.run`` but starts in *continue* mode (Bdb.run always starts by stepping)."""
        self.reset()
        self.botframe = sys._getframe()
        if stop_on_entry:
            self.set_step()
        else:
            self.set_continue()
        sys.settrace(self.trace_dispatch)
        try:
            exec(code, namespace, namespace)
        finally:
            self.quitting = True
            sys.settrace(None)

    def _pause(self, frame, reason, return_value=None):
        stack, _ = self.get_stack(frame, None)
        frames = []
        for f, line in reversed(stack):
            if self._is_internal(f):
                continue
            frames.append({
                "file": os.path.abspath(f.f_code.co_filename) if not f.f_code.co_filename.startswith("<")
                else f.f_code.co_filename,
                "line": line,
                "name": f.f_code.co_name,
                "vars": _frame_variables(f),
            })
        message = {"event": "paused", "reason": reason, "stack": frames}
        if reason == "return":
            message["return_value"] = _safe_repr(return_value)
        self.connection.send(message)
        cmd = self._commands.get()
        if cmd == "step":
            self.set_step()
        elif cmd == "next":
            self.set_next(frame)
        elif cmd == "out":
            self._out_frame = frame
            self.set_return(frame)
        else:
            self.set_continue()


def main(argv):
    port, token, script, args = int(argv[1]), argv[2], os.path.abspath(argv[3]), argv[4:]

    connection = Connection(port, token)
    debugger = IdeDebugger(connection, script)
    start = next(connection.messages())          # {"cmd": "start", "breakpoints": {...}, "entry": bool}
    debugger.apply_breakpoints(start.get("breakpoints", {}))
    stop_on_entry = bool(start.get("entry"))
    threading.Thread(target=debugger.listen, daemon=True).start()

    sys.argv = [script] + args
    sys.path[0] = os.path.dirname(script)
    with open(script, "rb") as handle:
        source = handle.read()
    code = compile(source, script, "exec")
    namespace = {"__name__": "__main__", "__file__": script, "__builtins__": __builtins__,
                 "__doc__": None, "__package__": None}
    exit_code = 0
    try:
        debugger.run_code(code, namespace, stop_on_entry)
    except bdb.BdbQuit:
        pass
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BaseException:  # noqa: BLE001 - print like the normal interpreter would
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    main(sys.argv)
