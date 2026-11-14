"""Headless tests for core/debug_worker.py (no Qt): the test plays the role of the IDE."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import unittest

WORKER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "debug_worker.py")
SCRIPT = textwrap.dedent('''\
    def add(a, b):
        total = a + b
        return total

    x = 1
    y = add(x, 41)
    print("result", y)
''')


class FakeIde:
    def __init__(self, script, breakpoints, entry=False):
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.server.settimeout(15)
        port = self.server.getsockname()[1]
        self.proc = subprocess.Popen(
            [sys.executable, "-u", WORKER, str(port), "tok", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.conn, _ = self.server.accept()
        self.conn.settimeout(15)
        self.reader = self.conn.makefile("r", encoding="utf-8")
        hello = self.read()
        assert hello["event"] == "hello" and hello["token"] == "tok"
        self.send({"cmd": "start", "breakpoints": breakpoints, "entry": entry})

    def read(self):
        return json.loads(self.reader.readline())

    def send(self, message):
        self.conn.sendall((json.dumps(message) + "\n").encode())

    def finish(self):
        out, err = self.proc.communicate(timeout=15)
        self.reader.close()
        self.conn.close()
        self.server.close()
        return self.proc.returncode, out, err


class DebugWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.script = os.path.join(self.tmp.name, "prog.py")
        with open(self.script, "w", encoding="utf-8") as handle:
            handle.write(SCRIPT)

    def tearDown(self):
        self.tmp.cleanup()

    def test_breakpoint_variables_and_continue(self):
        ide = FakeIde(self.script, {self.script: [2]})
        pause = ide.read()
        self.assertEqual(pause["event"], "paused")
        self.assertEqual(pause["reason"], "breakpoint")
        top = pause["stack"][0]
        self.assertEqual((top["name"], top["line"]), ("add", 2))
        self.assertEqual({v[0]: v[2] for v in top["vars"]}, {"a": "1", "b": "41"})
        self.assertEqual(pause["stack"][1]["name"], "<module>")
        ide.send({"cmd": "continue"})
        code, out, _ = ide.finish()
        self.assertEqual(code, 0)
        self.assertIn("result 42", out)

    def test_step_over_and_step_out(self):
        ide = FakeIde(self.script, {self.script: [2]})
        ide.read()
        ide.send({"cmd": "next"})
        pause = ide.read()
        self.assertEqual(pause["stack"][0]["line"], 3)
        self.assertEqual({v[0]: v[2] for v in pause["stack"][0]["vars"]}["total"], "42")
        ide.send({"cmd": "out"})
        pause = ide.read()
        self.assertEqual((pause["stack"][0]["name"], pause["stack"][0]["line"]), ("<module>", 7))
        ide.send({"cmd": "continue"})
        self.assertEqual(ide.finish()[0], 0)

    def test_step_into_and_stop_on_entry(self):
        ide = FakeIde(self.script, {}, entry=True)
        pause = ide.read()
        self.assertEqual(pause["stack"][0]["name"], "<module>")
        self.assertEqual(pause["stack"][0]["line"], 1)
        for _ in range(2):          # line 1 -> 5 -> 6
            ide.send({"cmd": "step"})
            pause = ide.read()
        self.assertEqual(pause["stack"][0]["line"], 6)
        ide.send({"cmd": "step"})
        pause = ide.read()
        self.assertEqual(pause["stack"][0]["name"], "add")
        ide.send({"cmd": "continue"})
        self.assertEqual(ide.finish()[0], 0)

    def test_runs_to_end_without_breakpoints_and_reports_exit_code(self):
        with open(self.script, "w", encoding="utf-8") as handle:
            handle.write("import sys\nprint('bye')\nsys.exit(3)\n")
        ide = FakeIde(self.script, {})
        code, out, _ = ide.finish()
        self.assertEqual(code, 3)
        self.assertIn("bye", out)

    def test_uncaught_exception_prints_traceback(self):
        with open(self.script, "w", encoding="utf-8") as handle:
            handle.write("raise ValueError('boom')\n")
        ide = FakeIde(self.script, {})
        code, _, err = ide.finish()
        self.assertEqual(code, 1)
        self.assertIn("ValueError: boom", err)

    def test_breakpoints_can_be_added_while_paused(self):
        ide = FakeIde(self.script, {self.script: [2]})
        ide.read()
        ide.send({"cmd": "breakpoints", "files": {self.script: [7]}})
        ide.send({"cmd": "continue"})
        pause = ide.read()
        self.assertEqual((pause["stack"][0]["name"], pause["stack"][0]["line"]), ("<module>", 7))
        ide.send({"cmd": "continue"})
        self.assertEqual(ide.finish()[0], 0)

    def test_worker_exits_when_ide_disconnects(self):
        ide = FakeIde(self.script, {self.script: [2]})
        ide.read()
        ide.reader.close()
        ide.conn.close()
        self.assertEqual(ide.proc.wait(timeout=15), 1)
        ide.proc.stdout.close()
        ide.proc.stderr.close()
        ide.server.close()


if __name__ == "__main__":
    unittest.main()
