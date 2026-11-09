"""Small pure helpers shared by the UI (no Qt imports)."""
import os
import re

from dataclasses import dataclass


# ------------------------------------------------------------------ search ----

def build_pattern(text, case_sensitive=False, whole_word=False, regex=False):
    """Compile a user query into a Python regex. Raises ``re.error`` for bad regexes."""
    if not text:
        raise ValueError("empty pattern")
    body = text if regex else re.escape(text)
    if whole_word:
        body = rf"(?<!\w)(?:{body})(?!\w)"
    flags = re.MULTILINE
    if not case_sensitive:
        flags |= re.IGNORECASE
    return re.compile(body, flags)


def expand_replacement(match, replacement, regex):
    """Return the replacement text for ``match`` (supports \\1, \\g<name> in regex mode)."""
    if not regex:
        return replacement
    try:
        return match.expand(replacement)
    except (re.error, IndexError):
        return replacement


# ------------------------------------------------------------------- fuzzy ----

def fuzzy_score(query, candidate):
    """Subsequence score (higher is better) or None when ``query`` does not match."""
    if not query:
        return 0
    q = query.lower()
    c = candidate.lower()
    score = 0
    pos = 0
    prev = -2
    for ch in q:
        idx = c.find(ch, pos)
        if idx < 0:
            return None
        score += 10
        if idx == prev + 1:
            score += 8                       # consecutive characters
        if idx == 0 or not c[idx - 1].isalnum():
            score += 6                       # start of a word / path segment
        score -= min(idx - pos, 5)           # gaps cost a little
        prev = idx
        pos = idx + 1
    if q in c:
        score += 25                          # contiguous substring
    if c.startswith(q):
        score += 15
    score -= len(c) // 12                    # prefer shorter candidates
    return score


def fuzzy_filter(query, items, key=lambda item: item, limit=200):
    """Return items matching ``query`` ordered by score (stable for empty queries)."""
    if not query.strip():
        return list(items)[:limit]
    scored = []
    for order, item in enumerate(items):
        score = fuzzy_score(query.strip(), key(item))
        if score is not None:
            scored.append((-score, order, item))
    scored.sort(key=lambda entry: (entry[0], entry[1]))
    return [entry[2] for entry in scored[:limit]]


# ----------------------------------------------------------------- file io ----

class BinaryFileError(Exception):
    """Raised when a file looks binary and should not be opened as text."""


@dataclass
class LoadedText:
    text: str
    encoding: str
    eol: str          # "\n", "\r\n" or "\r"


def detect_eol(text):
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    if crlf == 0 and lf == 0 and cr == 0:
        return "\n"
    if crlf >= lf and crlf >= cr:
        return "\r\n"
    return "\n" if lf >= cr else "\r"


def read_text_file(path, max_bytes=50 * 1024 * 1024):
    size = os.path.getsize(path)
    if size > max_bytes:
        raise BinaryFileError(f"File is too large to open ({size // (1024 * 1024)} MB).")
    with open(path, "rb") as handle:
        raw = handle.read()
    if b"\x00" in raw[:8192] and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise BinaryFileError("This looks like a binary file.")
    if raw.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    else:
        encoding = "utf-8"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
        text = raw.decode(encoding)
    return LoadedText(text, encoding, detect_eol(text))


def write_text_file(path, text, encoding="utf-8"):
    """Write text exactly as given (no newline translation)."""
    with open(path, "wb") as handle:
        handle.write(text.encode(encoding, errors="replace"))


def apply_save_transforms(text, trim_trailing=False, final_newline=False, eol="\n"):
    """Optional clean-ups performed right before saving."""
    if trim_trailing:
        text = re.sub(r"[ \t]+(?=\r?$)", "", text, flags=re.MULTILINE)
    if final_newline and text and not text.endswith(("\n", "\r")):
        text += eol
    return text


# ------------------------------------------------------------------- misc ----

def console_encoding():
    """Encoding used by the platform shell for its output."""
    if os.name == "nt":
        try:
            import ctypes
            return f"cp{ctypes.windll.kernel32.GetOEMCP()}"
        except Exception:
            return "cp437"
    return "utf-8"


def format_duration(seconds):
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)} min {rest:.0f} s"


EOL_NAMES = {"\n": "LF", "\r\n": "CRLF", "\r": "CR"}


_LOCATION_PATTERNS = (
    re.compile(r'File "(?P<path>[^"]+)", line (?P<line>\d+)'),                        # Python traceback
    re.compile(r'(?P<path>[A-Za-z]:[\\/][^:\r\n"\'<>|*?]+?):(?P<line>\d+)(?::(?P<col>\d+))?'),   # C:\x\y.c:12:3
    re.compile(r'(?P<path>(?:\.{0,2}[\\/])?[^\s:"\'()<>|*?]+\.[A-Za-z0-9_+]+):(?P<line>\d+)(?::(?P<col>\d+))?'),  # gcc, node, rustc
)


def parse_location(text):
    """Find a ``file:line`` reference in a console line. Returns (path, line, column|None) or None."""
    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(text)
        if match:
            column = match.groupdict().get("col")
            return match.group("path"), int(match.group("line")), int(column) if column else None
    return None
