"""Code analysis helpers: syntax checks, outline symbols, formatting, workspace search.

Pure Python (no Qt) so everything here can be unit-tested headlessly.
"""
import ast
import fnmatch
import io
import json
import os
import re
import tokenize
from dataclasses import dataclass

@dataclass
class Problem:
    line: int          # 1-based
    column: int        # 1-based
    message: str
    severity: str = "error"

def check_syntax(text, language_key):
    """Return a list of Problems for languages we can validate cheaply and reliably."""
    problems = []
    if language_key == "python":
        try:
            compile(text, "<editor>", "exec", flags=ast.PyCF_ONLY_AST)
        except SyntaxError as exc:
            line = exc.lineno or 1
            problems.append(Problem(line, max(1, exc.offset or 1), exc.msg or "Syntax error"))
        except (ValueError, MemoryError, RecursionError) as exc:
            problems.append(Problem(1, 1, str(exc)))
    elif language_key == "json":
        if text.strip():
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                problems.append(Problem(exc.lineno, exc.colno, exc.msg))
    return problems

@dataclass
class Symbol:
    kind: str          # class, function, method, heading, selector, table ...
    name: str
    line: int          # 0-based
    level: int = 0

_CALL_KEYWORDS = {"if", "for", "while", "switch", "return", "else", "catch", "sizeof", "new", "do", "case"}

_PY_DEF = re.compile(r"^(\s*)(?:async\s+def|def|class)\s+(\w+)")
_JS_PATTERNS = [
    ("class", re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\*?\s+(\w+)")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function")),
    ("interface", re.compile(r"^\s*(?:export\s+)?(?:interface|type|enum)\s+(\w+)")),
]
_C_PATTERNS = [
    ("class", re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+|sealed\s+)*(?:class|struct|interface|enum|namespace)\s+(\w+)")),
    ("function", re.compile(r"^[A-Za-z_][\w:<>,\*&\s]*?[\s\*&]([A-Za-z_~]\w*)\s*\([^;{}]*\)\s*(?:const|override|noexcept|final|throws[\w\s,]*)?\s*\{?\s*$")),
]
_GO_PATTERNS = [
    ("function", re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)")),
    ("class", re.compile(r"^type\s+(\w+)\s+(?:struct|interface)")),
]
_RUST_PATTERNS = [
    ("function", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)")),
    ("class", re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait|impl|mod)\s+(\w+)")),
]
_PHP_PATTERNS = [
    ("class", re.compile(r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait)\s+(\w+)")),
    ("function", re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+)*function\s+&?(\w+)")),
]
_RUBY_PATTERNS = [
    ("class", re.compile(r"^\s*(?:class|module)\s+([\w:]+)")),
    ("function", re.compile(r"^\s*def\s+(?:self\.)?(\w+[?!=]?)")),
]
_LUA_PATTERNS = [("function", re.compile(r"^\s*(?:local\s+)?function\s+([\w.:]+)"))]
_BASH_PATTERNS = [("function", re.compile(r"^\s*(?:function\s+)?([\w-]+)\s*\(\)\s*\{?"))]
_SQL_PATTERNS = [("table", re.compile(
    r"^\s*create\s+(?:or\s+replace\s+)?(?:temporary\s+)?(?:table|view|function|procedure|index|trigger)\s+(?:if\s+not\s+exists\s+)?([\w.\"`]+)",
    re.IGNORECASE))]
_PATTERNS_BY_LANG = {
    "javascript": _JS_PATTERNS, "typescript": _JS_PATTERNS,
    "c": _C_PATTERNS, "cpp": _C_PATTERNS, "java": _C_PATTERNS, "csharp": _C_PATTERNS,
    "go": _GO_PATTERNS, "rust": _RUST_PATTERNS, "php": _PHP_PATTERNS,
    "ruby": _RUBY_PATTERNS, "lua": _LUA_PATTERNS, "bash": _BASH_PATTERNS, "sql": _SQL_PATTERNS,
}

def extract_symbols(text, language_key):
    lines = text.splitlines()
    symbols = []
    if language_key == "python":
        stack = []  # (indent, kind)
        for number, line in enumerate(lines):
            match = _PY_DEF.match(line)
            if not match:
                continue
            indent = len(match.group(1).expandtabs(4))
            while stack and stack[-1][0] >= indent:
                stack.pop()
            is_class = line.lstrip().startswith("class ")
            kind = "class" if is_class else ("method" if stack and stack[-1][1] == "class" else "function")
            symbols.append(Symbol(kind, match.group(2), number, len(stack)))
            stack.append((indent, "class" if is_class else "function"))
    elif language_key in ("markdown",):
        in_fence = False
        for number, line in enumerate(lines):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
            if in_fence:
                continue
            match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match:
                symbols.append(Symbol("heading", match.group(2), number, len(match.group(1)) - 1))
    elif language_key == "html":
        for number, line in enumerate(lines):
            for match in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", line, re.IGNORECASE):
                label = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if label:
                    symbols.append(Symbol("heading", label, number, int(match.group(1)) - 1))
            match = re.search(r"<(?:section|nav|header|footer|main|form)\b[^>]*\bid=[\"']([^\"']+)", line, re.IGNORECASE)
            if match:
                symbols.append(Symbol("selector", "#" + match.group(1), number, 0))
    elif language_key in ("css", "scss"):
        for number, line in enumerate(lines):
            match = re.match(r"^([^\s@/}{][^{};]*?)\s*\{\s*$", line)
            if match:
                symbols.append(Symbol("selector", match.group(1).strip(), number, 0))
            elif line.startswith("@media") or line.startswith("@keyframes"):
                symbols.append(Symbol("selector", line.split("{")[0].strip(), number, 0))
    elif language_key in _PATTERNS_BY_LANG:
        patterns = _PATTERNS_BY_LANG[language_key]
        for number, line in enumerate(lines):
            if line.lstrip().startswith(("//", "#", "*", "/*", "--")) and language_key != "bash":
                continue
            for kind, pattern in patterns:
                match = pattern.match(line)
                if match:
                    name = match.group(1)
                    if name in _CALL_KEYWORDS:
                        continue
                    indent = len(line) - len(line.lstrip())
                    symbols.append(Symbol(kind, name, number, min(indent // 4, 3)))
                    break
    return symbols

def _python_protected_lines(text):
    """Line numbers (1-based) inside multi-line strings, whose whitespace must stay untouched."""
    protected = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            name = tokenize.tok_name.get(tok.type, "")
            if name in ("STRING", "FSTRING_MIDDLE") and tok.start[0] != tok.end[0]:
                protected.update(range(tok.start[0], tok.end[0]))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return protected

def _python_builtin_format(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    protected = _python_protected_lines("\n".join(lines))
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError:
        tree = None

    starts = {}  # line (1-based) -> blank lines required before it
    if tree is not None:
        top_level = set(id(node) for node in tree.body)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = min([d.lineno for d in node.decorator_list] + [node.lineno])
                starts[first] = 2 if id(node) in top_level else 1

    out = []
    blank_run = 0
    for number, raw in enumerate(lines, start=1):
        protected_line = number in protected
        line = raw if protected_line else raw.rstrip()
        if line.strip() == "" and not protected_line:
            blank_run += 1
            continue
        if out:
            previous = out[-1].strip()
            required = starts.get(number)
            if required is not None:
                if previous.endswith(":"):
                    blanks = 0                      # first statement of a block
                elif previous.startswith("#") and blank_run == 0:
                    blanks = 0                      # comment attached to the definition
                else:
                    blanks = required
            else:
                indented = line[:1] in (" ", "\t")
                blanks = min(blank_run, 1 if indented else 2)
            out.extend([""] * blanks)
        blank_run = 0
        out.append(line)
    return ("\n".join(out).rstrip("\n") + "\n") if out else ""


def _run_black(text):
    """Format with Black in-process (works from source and in the PyInstaller build)."""
    try:
        import black
    except ImportError:
        return None
    try:
        formatted = black.format_str(text, mode=black.Mode())
    except Exception:  # noqa: BLE001 - invalid source or an unsupported Black version: fall back
        return None
    return formatted or None


def format_source(text, language_key):
    """Return (formatted_text, engine_name)."""
    if language_key == "python":
        formatted = _run_black(text)
        if formatted is not None:
            return formatted, "black"
        return _python_builtin_format(text), "built-in"
    if language_key == "json" and text.strip():
        try:
            return json.dumps(json.loads(text), indent=4, ensure_ascii=False) + "\n", "json"
        except ValueError:
            pass
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n") if lines else "", "whitespace"

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env", ".idea", ".vscode",
    "dist", "build", ".gradle", ".mypy_cache", ".pytest_cache", ".tox", "target", ".cache", ".next",
}
MAX_SEARCH_FILE_BYTES = 2 * 1024 * 1024

def _looks_binary(path):
    try:
        with open(path, "rb") as handle:
            return b"\x00" in handle.read(4096)
    except OSError:
        return True

def _matches_globs(name, globs):
    return not globs or any(fnmatch.fnmatch(name.lower(), g.lower()) for g in globs)

def parse_globs(text):
    return [part.strip() for part in re.split(r"[,;\s]+", text or "") if part.strip()]

def iter_workspace_files(root, globs=(), limit=50000):
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.endswith(".egg-info"))
        for name in sorted(files):
            if not _matches_globs(name, globs):
                continue
            yield os.path.join(current, name)
            count += 1
            if count >= limit:
                return

def list_workspace_files(root, limit=20000):
    """Relative paths (forward slashes) used by the Quick Open palette."""
    result = []
    for path in iter_workspace_files(root, limit=limit):
        result.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return result

def search_in_files(root, pattern, globs=(), max_results=2000):
    """Yield (path, line_number, line_text, start, end) for every match under ``root``."""
    found = 0
    for path in iter_workspace_files(root, globs):
        try:
            if os.path.getsize(path) > MAX_SEARCH_FILE_BYTES or _looks_binary(path):
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for number, line in enumerate(handle, start=1):
                    text = line.rstrip("\r\n")
                    for match in pattern.finditer(text):
                        if match.end() == match.start():
                            continue
                        yield path, number, text, match.start(), match.end()
                        found += 1
                        if found >= max_results:
                            return
        except OSError:
            continue
