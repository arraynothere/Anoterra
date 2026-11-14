"""Language registry and run-command planning (no Qt imports, fully testable)."""
import builtins
import keyword
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Language:
    key: str
    name: str
    extensions: tuple = ()
    filenames: tuple = ()
    lexer: str = ""              # QsciLexer class name, "" = plain text
    comment: str = ""            # line comment prefix
    block_comment: tuple = ()    # (open, close) used when no line comment exists
    colon_indent: bool = False   # trailing ':' opens an indented block
    brace_indent: bool = True    # trailing { ( [ opens an indented block
    keywords: tuple = ()

_JS_WORDS = (
    "function", "const", "let", "var", "return", "if", "else", "for", "while", "do", "switch", "case",
    "break", "continue", "class", "extends", "new", "this", "super", "import", "export", "default",
    "async", "await", "try", "catch", "finally", "throw", "typeof", "instanceof", "null", "undefined",
    "true", "false", "console.log", "document.getElementById", "document.querySelector", "addEventListener",
    "setTimeout", "setInterval", "Promise", "JSON.stringify", "JSON.parse", "Array", "Object", "Map", "Set",
)
_C_WORDS = (
    "int", "long", "short", "float", "double", "char", "void", "bool", "unsigned", "signed", "const", "static",
    "struct", "union", "enum", "typedef", "return", "if", "else", "for", "while", "do", "switch", "case",
    "break", "continue", "default", "sizeof", "include", "define", "NULL", "printf", "scanf", "malloc", "free",
)
_CPP_WORDS = _C_WORDS + (
    "class", "public", "private", "protected", "namespace", "using", "template", "typename", "virtual",
    "override", "auto", "nullptr", "new", "delete", "try", "catch", "throw", "std::cout", "std::cin",
    "std::string", "std::vector", "std::map", "std::endl", "constexpr",
)
_JAVA_WORDS = (
    "public", "private", "protected", "class", "interface", "extends", "implements", "static", "final",
    "void", "int", "long", "double", "boolean", "String", "return", "if", "else", "for", "while", "switch",
    "case", "break", "continue", "new", "this", "super", "try", "catch", "finally", "throw", "throws",
    "import", "package", "System.out.println", "ArrayList", "HashMap", "List", "Map",
)
_CSS_WORDS = (
    "color", "background", "background-color", "margin", "padding", "border", "border-radius", "font-size",
    "font-family", "font-weight", "display", "flex", "grid", "position", "width", "height", "min-width",
    "max-width", "top", "left", "right", "bottom", "text-align", "justify-content", "align-items",
    "gap", "overflow", "transition", "transform", "opacity", "z-index", "box-shadow", "cursor",
)
_HTML_WORDS = (
    "<!DOCTYPE html>", "<html>", "<head>", "<meta>", "<title>", "<body>", "<div>", "<span>", "<a>", "<p>",
    "<h1>", "<h2>", "<h3>", "<ul>", "<ol>", "<li>", "<table>", "<tr>", "<td>", "<form>", "<input>",
    "<button>", "<img>", "<script>", "<style>", "<link>", "class", "id", "style", "src", "href", "alt",
)
_SQL_WORDS = (
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE", "TABLE",
    "ALTER", "DROP", "INDEX", "VIEW", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "GROUP", "BY",
    "ORDER", "HAVING", "LIMIT", "DISTINCT", "UNION", "AS", "AND", "OR", "NOT", "NULL", "COUNT", "SUM", "AVG",
)
_BASH_WORDS = (
    "if", "then", "else", "elif", "fi", "for", "while", "do", "done", "case", "esac", "function", "echo",
    "export", "local", "return", "exit", "source", "read", "grep", "sed", "awk", "cat", "ls", "cd", "mkdir",
)
_GO_WORDS = (
    "package", "import", "func", "var", "const", "type", "struct", "interface", "map", "chan", "go", "defer",
    "return", "if", "else", "for", "range", "switch", "case", "select", "fmt.Println", "fmt.Printf", "nil",
)
_RUST_WORDS = (
    "fn", "let", "mut", "const", "static", "struct", "enum", "impl", "trait", "pub", "use", "mod", "match",
    "if", "else", "for", "while", "loop", "return", "self", "Self", "Some", "None", "Ok", "Err", "println!",
    "String", "Vec", "Option", "Result",
)
_PHP_WORDS = (
    "<?php", "function", "class", "public", "private", "protected", "static", "return", "if", "else",
    "foreach", "while", "echo", "require", "include", "namespace", "use", "array", "isset", "empty",
)

def _python_words():
    names = [n for n in dir(builtins) if not n.startswith("_")]
    return tuple(sorted(set(keyword.kwlist + names + ["self", "__init__", "__name__", "__main__"])))

LANGUAGES = [
    Language("python", "Python", (".py", ".pyw", ".pyi"), (), "QsciLexerPython", "#", (), True, True, _python_words()),
    Language("javascript", "JavaScript", (".js", ".mjs", ".cjs", ".jsx"), (), "QsciLexerJavaScript", "//", (), False, True, _JS_WORDS),
    Language("typescript", "TypeScript", (".ts", ".tsx"), (), "QsciLexerJavaScript", "//", (), False, True, _JS_WORDS + ("interface", "type", "enum", "readonly", "string", "number", "boolean")),
    Language("c", "C", (".c", ".h"), (), "QsciLexerCPP", "//", (), False, True, _C_WORDS),
    Language("cpp", "C++", (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"), (), "QsciLexerCPP", "//", (), False, True, _CPP_WORDS),
    Language("csharp", "C#", (".cs",), (), "QsciLexerCSharp", "//", (), False, True, _JAVA_WORDS + ("namespace", "using", "var", "async", "await", "Console.WriteLine")),
    Language("java", "Java", (".java",), (), "QsciLexerJava", "//", (), False, True, _JAVA_WORDS),
    Language("go", "Go", (".go",), (), "QsciLexerCPP", "//", (), False, True, _GO_WORDS),
    Language("rust", "Rust", (".rs",), (), "QsciLexerCPP", "//", (), False, True, _RUST_WORDS),
    Language("php", "PHP", (".php", ".phtml"), (), "QsciLexerHTML", "//", (), False, True, _PHP_WORDS),
    Language("html", "HTML", (".html", ".htm", ".xhtml"), (), "QsciLexerHTML", "", ("<!--", "-->"), False, True, _HTML_WORDS),
    Language("css", "CSS", (".css",), (), "QsciLexerCSS", "", ("/*", "*/"), False, True, _CSS_WORDS),
    Language("scss", "SCSS / Less", (".scss", ".sass", ".less"), (), "QsciLexerCSS", "//", (), False, True, _CSS_WORDS),
    Language("json", "JSON", (".json", ".jsonc", ".webmanifest"), (".babelrc", ".eslintrc"), "QsciLexerJSON", "", (), False, True, ("true", "false", "null")),
    Language("xml", "XML", (".xml", ".svg", ".xaml", ".xsl", ".plist", ".csproj"), (), "QsciLexerXML", "", ("<!--", "-->"), False, False, ()),
    Language("yaml", "YAML", (".yml", ".yaml"), (), "QsciLexerYAML", "#", (), True, False, ("true", "false", "null")),
    Language("markdown", "Markdown", (".md", ".markdown", ".mdx"), (), "QsciLexerMarkdown", "", ("<!--", "-->"), False, False, ()),
    Language("sql", "SQL", (".sql",), (), "QsciLexerSQL", "--", (), False, True, _SQL_WORDS),
    Language("bash", "Shell", (".sh", ".bash", ".zsh"), (".bashrc", ".zshrc", ".profile"), "QsciLexerBash", "#", (), False, False, _BASH_WORDS),
    Language("batch", "Batch", (".bat", ".cmd"), (), "QsciLexerBatch", "REM ", (), False, False, ("echo", "set", "if", "else", "goto", "call", "exit", "pause", "for", "rem")),
    Language("powershell", "PowerShell", (".ps1", ".psm1"), (), "", "#", (), False, True, ("Write-Host", "Get-ChildItem", "Set-Location", "function", "param", "foreach", "if", "else")),
    Language("lua", "Lua", (".lua",), (), "QsciLexerLua", "--", (), False, False, ("function", "end", "local", "if", "then", "else", "elseif", "for", "while", "do", "return", "print", "nil")),
    Language("ruby", "Ruby", (".rb", ".rake", ".gemspec"), ("Rakefile", "Gemfile"), "QsciLexerRuby", "#", (), False, False, ("def", "end", "class", "module", "if", "elsif", "else", "unless", "while", "do", "puts", "require", "attr_accessor")),
    Language("perl", "Perl", (".pl", ".pm"), (), "QsciLexerPerl", "#", (), False, True, ("my", "our", "sub", "use", "strict", "warnings", "print", "foreach", "if", "else")),
    Language("ini", "INI / TOML", (".ini", ".cfg", ".conf", ".toml", ".properties", ".env"), (), "QsciLexerProperties", "#", (), False, False, ()),
    Language("makefile", "Makefile", (".mk",), ("Makefile", "makefile", "GNUmakefile"), "QsciLexerMakefile", "#", (), False, False, ()),
    Language("cmake", "CMake", (".cmake",), ("CMakeLists.txt",), "QsciLexerCMake", "#", (), False, False, ("cmake_minimum_required", "project", "add_executable", "add_library", "target_link_libraries")),
    Language("diff", "Diff", (".diff", ".patch"), (), "QsciLexerDiff", "", (), False, False, ()),
    Language("tex", "LaTeX", (".tex", ".sty"), (), "QsciLexerTeX", "%", (), False, False, ()),
    Language("text", "Plain Text", (".txt", ".log", ".text"), (), "", "", (), False, False, ()),
]

LANGUAGE_BY_KEY = {lang.key: lang for lang in LANGUAGES}
_BY_EXT = {}
_BY_NAME = {}
for _lang in LANGUAGES:
    for _ext in _lang.extensions:
        _BY_EXT.setdefault(_ext, _lang)
    for _name in _lang.filenames:
        _BY_NAME[_name.lower()] = _lang

TEXT = LANGUAGE_BY_KEY["text"]
PYTHON = LANGUAGE_BY_KEY["python"]

def detect_language(path_or_name, default=None):
    """Return the Language for a path / title. Unknown names fall back to ``default`` (Python)."""
    if not path_or_name:
        return default or PYTHON
    base = os.path.basename(str(path_or_name))
    by_name = _BY_NAME.get(base.lower())
    if by_name:
        return by_name
    ext = os.path.splitext(base)[1].lower()
    if ext in _BY_EXT:
        return _BY_EXT[ext]
    return default or TEXT

class RunError(Exception):
    """Raised when a file cannot be run (missing toolchain, unsupported type)."""

@dataclass
class RunPlan:
    steps: list = field(default_factory=list)   # compile commands, executed in order
    run: list = field(default_factory=list)     # final command
    cleanup_dir: str = ""
    label: str = ""

def find_python(custom=None):
    """Interpreter used to run .py files. When frozen, sys.executable is Anoterra itself."""
    if custom and os.path.exists(custom):
        return custom
    if not getattr(sys, "frozen", False):
        return sys.executable
    for name in ("python", "python3", "py"):
        found = shutil.which(name)
        if found:
            return found
    raise RunError("Python was not found in PATH. Install Python or set an interpreter in Settings.")

def _need(*tools):
    for tool in tools:
        found = shutil.which(tool)
        if found:
            return found
    names = " / ".join(tools)
    raise RunError(f"'{names}' was not found in PATH. Install it to run this kind of file.")

def run_plan(file_path, python_exe=None, debug=False, args=None):
    """Build the commands needed to run ``file_path``; raises RunError when impossible."""
    args = list(args or [])
    ext = os.path.splitext(file_path)[1].lower()
    exe_ext = ".exe" if os.name == "nt" else ""

    if ext in (".py", ".pyw", ".pyi"):
        py = find_python(python_exe)
        cmd = [py, "-u"] + (["-X", "dev"] if debug else []) + [file_path] + args
        return RunPlan(run=cmd, label="Python")
    if ext in (".js", ".mjs", ".cjs"):
        return RunPlan(run=[_need("node"), file_path] + args, label="Node.js")
    if ext == ".ts":
        tool = _need("tsx", "ts-node", "deno")
        if os.path.basename(tool).lower().startswith("deno"):
            return RunPlan(run=[tool, "run", "-A", file_path] + args, label="Deno")
        return RunPlan(run=[tool, file_path] + args, label="TypeScript")
    if ext in (".c", ".cpp", ".cc", ".cxx"):
        if ext == ".c":
            compiler = _need("gcc", "clang", "cc")
        else:
            compiler = _need("g++", "clang++", "c++")
        out_dir = tempfile.mkdtemp(prefix="anoterra_")
        out_bin = os.path.join(out_dir, "program" + exe_ext)
        flags = ["-g", "-Wall"] if debug else ["-O1"]
        return RunPlan(steps=[[compiler, file_path, "-o", out_bin] + flags], run=[out_bin] + args,
                       cleanup_dir=out_dir, label="C" if ext == ".c" else "C++")
    if ext == ".rs":
        rustc = _need("rustc")
        out_dir = tempfile.mkdtemp(prefix="anoterra_")
        out_bin = os.path.join(out_dir, "program" + exe_ext)
        return RunPlan(steps=[[rustc, file_path, "-o", out_bin]], run=[out_bin] + args,
                       cleanup_dir=out_dir, label="Rust")
    if ext == ".go":
        return RunPlan(run=[_need("go"), "run", file_path] + args, label="Go")
    if ext == ".java":
        return RunPlan(run=[_need("java"), file_path] + args, label="Java")
    if ext == ".php":
        return RunPlan(run=[_need("php"), file_path] + args, label="PHP")
    if ext == ".rb":
        return RunPlan(run=[_need("ruby"), file_path] + args, label="Ruby")
    if ext == ".lua":
        return RunPlan(run=[_need("lua", "luajit"), file_path] + args, label="Lua")
    if ext in (".pl", ".pm"):
        return RunPlan(run=[_need("perl"), file_path] + args, label="Perl")
    if ext in (".sh", ".bash", ".zsh"):
        return RunPlan(run=[_need("bash", "sh"), file_path] + args, label="Shell")
    if ext in (".bat", ".cmd"):
        if os.name != "nt":
            raise RunError("Batch files can only be run on Windows.")
        return RunPlan(run=["cmd", "/c", file_path] + args, label="Batch")
    if ext in (".ps1",):
        shell = _need("pwsh", "powershell")
        return RunPlan(run=[shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", file_path] + args,
                       label="PowerShell")
    raise RunError(f"No runner is configured for '{ext or os.path.basename(file_path)}' files.")
