import os
import re

from PyQt6 import Qsci
from PyQt6.Qsci import QsciScintilla, QsciAPIs
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QKeyEvent

from core.analysis import format_source
from core.languages import LANGUAGE_BY_KEY, PYTHON, detect_language
from core.settings import DEFAULTS, EDITOR_KEYS
from core.theme_data import EDITOR_PALETTES, classify_style
from core.utils import build_pattern, expand_replacement

MARKER_BOOKMARK = 1
MARKER_ERROR = 2
IND_MATCH = 8
IND_WORD = 9
IND_ERROR = 10

_OPENERS = {"(": ")", "[": "]", "{": "}"}
_QUOTES = ("'", '"', "`")
_CLOSERS = (")", "]", "}")
_PREFERRED_FONTS = ("Cascadia Code", "JetBrains Mono", "Fira Code", "Consolas", "DejaVu Sans Mono", "Menlo", "Courier New")
_font_families = None

def _installed_fonts():
    global _font_families
    if _font_families is None:
        _font_families = set(QFontDatabase.families())
    return _font_families

def pick_editor_font(family="", size=11):
    families = _installed_fonts()
    chosen = family if family and family in families else next((f for f in _PREFERRED_FONTS if f in families), "")
    font = QFont(chosen) if chosen else QFont()
    font.setPointSize(size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    return font

class AnoterraEditor(QsciScintilla):
    content_changed_signal = pyqtSignal(bool)
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None, file_path=None, language_hint=None):
        super().__init__(parent)
        self.file_path = file_path
        self.language_hint = language_hint
        self.forced_language = None
        self.theme_name = "dark"
        self.is_modified_flag = False
        self.lexer_instance = None
        self.api_instance = None
        self.language = PYTHON
        self.encoding = "utf-8"
        self.eol = "\n"
        self.disk_mtime = None
        self.problems = []
        self.options = {key: DEFAULTS[key] for key in EDITOR_KEYS}

        self._word_timer = QTimer(self)
        self._word_timer.setSingleShot(True)
        self._word_timer.setInterval(220)
        self._word_timer.timeout.connect(self._update_word_highlight)

        self.setAcceptDrops(True)
        self._configure_editor_base()
        self._configure_margins()
        self._configure_caret_and_selection()
        self._configure_folding()
        self._configure_indicators()
        self._configure_autocomplete()
        self._init_lexer()
        self.apply_options(self.options)
        self.set_eol("\r\n" if os.linesep == "\r\n" else "\n")
        self._connect_signals()

    def _sci(self, name, default, *args):
        return self.SendScintilla(getattr(self, name, default), *args)

    def _palette(self):
        return EDITOR_PALETTES[self.theme_name]

    def _configure_editor_base(self):
        self.setUtf8(True)
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setBackspaceUnindents(True)
        self.setTabIndents(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setScrollWidth(1)
        self.setScrollWidthTracking(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._sci("SCI_SETMULTIPLESELECTION", 2563, 1)
        self._sci("SCI_SETADDITIONALSELECTIONTYPING", 2565, 1)
        self._sci("SCI_SETMULTIPASTE", 2614, 1)

    def _configure_margins(self):
        palette = self._palette()
        font = self._get_optimal_font()
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginsForegroundColor(QColor(palette["margin_fg"]))
        self.setMarginsBackgroundColor(QColor(palette["margin_bg"]))
        self.setMarginsFont(font)
        self._update_margin_width()

        self.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(1, 16)
        self.setMarginSensitivity(1, True)
        self.setMarginMarkerMask(1, (1 << MARKER_BOOKMARK) | (1 << MARKER_ERROR))
        self.setMarginBackgroundColor(1, QColor(palette["margin_bg"]))
        self.markerDefine(QsciScintilla.MarkerSymbol.Circle, MARKER_BOOKMARK)
        self.setMarkerBackgroundColor(QColor(palette["bookmark"]), MARKER_BOOKMARK)
        self.setMarkerForegroundColor(QColor(palette["bookmark"]), MARKER_BOOKMARK)
        self.markerDefine(QsciScintilla.MarkerSymbol.Circle, MARKER_ERROR)
        self.setMarkerBackgroundColor(QColor(palette["error"]), MARKER_ERROR)
        self.setMarkerForegroundColor(QColor(palette["error"]), MARKER_ERROR)

    def _update_margin_width(self):
        if not self.options.get("show_line_numbers", True):
            self.setMarginWidth(0, 0)
            return
        digits = max(3, len(str(max(1, self.lines()))))
        self.setMarginWidth(0, "0" * (digits + 1))

    def _configure_caret_and_selection(self):
        palette = self._palette()
        self.setCaretForegroundColor(QColor(palette["caret"]))
        self.setCaretLineVisible(bool(self.options.get("caret_line", True)))
        self.setCaretLineBackgroundColor(QColor(palette["caret_line"]))
        self.setCaretWidth(2)
        self.setSelectionBackgroundColor(QColor(palette["sel_bg"]))
        self.setSelectionForegroundColor(QColor(palette["sel_fg"]))
        self.setMatchedBraceBackgroundColor(QColor(palette["brace_bg"]))
        self.setMatchedBraceForegroundColor(QColor(palette["brace_fg"]))
        self.setUnmatchedBraceBackgroundColor(QColor(palette["bad_brace_bg"]))
        self.setUnmatchedBraceForegroundColor(QColor(palette["bad_brace_fg"]))
        self.setIndentationGuidesBackgroundColor(QColor(palette["guide"]))
        self.setIndentationGuidesForegroundColor(QColor(palette["guide"]))
        self.setEdgeColor(QColor(palette["edge"]))
        self.setWhitespaceForegroundColor(QColor(palette["guide"]))
        self.setColor(QColor(palette["ed_fg"]))
        self.setPaper(QColor(palette["ed_bg"]))

    def _configure_folding(self):
        palette = self._palette()
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColors(QColor(palette["fold_bg"]), QColor(palette["fold_bg"]))

    def _configure_indicators(self):
        palette = self._palette()
        for number, key, style in (
            (IND_MATCH, "find_hl", QsciScintilla.IndicatorStyle.StraightBoxIndicator),
            (IND_WORD, "word_hl", QsciScintilla.IndicatorStyle.StraightBoxIndicator),
            (IND_ERROR, "error", QsciScintilla.IndicatorStyle.SquiggleIndicator),
        ):
            self.indicatorDefine(style, number)
            self.setIndicatorForegroundColor(QColor(palette[key]), number)
        self._sci("SCI_INDICSETALPHA", 2523, IND_MATCH, 150)
        self._sci("SCI_INDICSETALPHA", 2523, IND_WORD, 130)
        self._sci("SCI_INDICSETUNDER", 2510, IND_MATCH, 1)
        self._sci("SCI_INDICSETUNDER", 2510, IND_WORD, 1)

    def _configure_autocomplete(self):
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

    def apply_options(self, options):
        """Apply user preferences (fonts, indentation, visual aids)."""
        self.options.update({key: options[key] for key in EDITOR_KEYS if key in options})
        opts = self.options
        self.setTabWidth(int(opts["tab_width"]))
        self.setIndentationsUseTabs(bool(opts["use_tabs"]))
        self.setIndentationGuides(bool(opts["show_guides"]))
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord if opts["word_wrap"] else QsciScintilla.WrapMode.WrapNone)
        self.setWhitespaceVisibility(
            QsciScintilla.WhitespaceVisibility.WsVisible if opts["show_whitespace"]
            else QsciScintilla.WhitespaceVisibility.WsInvisible
        )
        if opts["show_edge"]:
            self.setEdgeMode(QsciScintilla.EdgeMode.EdgeLine)
            self.setEdgeColumn(int(opts["edge_column"]))
        else:
            self.setEdgeMode(QsciScintilla.EdgeMode.EdgeNone)
        self.setCaretLineVisible(bool(opts["caret_line"]))
        self._configure_margins()
        if self.lexer_instance is not None:
            self._apply_theme_to_lexer(self.lexer_instance, self._get_optimal_font())
        else:
            self.setFont(self._get_optimal_font())
        if not opts["highlight_words"]:
            self._clear_indicator(IND_WORD)

    def set_theme(self, theme_name):
        self.theme_name = theme_name if theme_name in EDITOR_PALETTES else "dark"
        self._configure_margins()
        self._configure_caret_and_selection()
        self._configure_folding()
        self._configure_indicators()
        if self.lexer_instance is not None:
            self._apply_theme_to_lexer(self.lexer_instance, self._get_optimal_font())
        self.set_problems(self.problems)

    def _init_lexer(self):
        hint = self.file_path or self.language_hint
        if self.forced_language:
            self.language = LANGUAGE_BY_KEY[self.forced_language]
        elif hint:
            self.language = detect_language(hint)
        else:
            self.language = PYTHON

        previous = self.lexer_instance
        lexer_cls = getattr(Qsci, self.language.lexer, None) if self.language.lexer else None
        font = self._get_optimal_font()
        if lexer_cls is not None:
            self.lexer_instance = lexer_cls(self)
            self._apply_theme_to_lexer(self.lexer_instance, font)
            self.setLexer(self.lexer_instance)
            self._setup_apis(self.lexer_instance)
        else:
            self.lexer_instance = None
            self.setLexer(None)
            self.setFont(font)
            self._configure_caret_and_selection()
            self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsDocument)
        if lexer_cls is not None:
            self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        if previous is not None:
            previous.deleteLater()
        self._update_margin_width()

    def set_file_path(self, file_path):
        self.file_path = file_path
        self.language_hint = file_path
        if not self.forced_language:
            self._init_lexer()

    def set_language(self, language_key):
        """Force a language (None re-detects from the file name)."""
        self.forced_language = language_key if language_key in LANGUAGE_BY_KEY else None
        self._init_lexer()

    def _apply_theme_to_lexer(self, lexer, font):
        palette = self._palette()
        paper = QColor(palette["ed_bg"])
        lexer.setDefaultFont(font)
        lexer.setDefaultColor(QColor(palette["ed_fg"]))
        lexer.setDefaultPaper(paper)
        lexer.setFont(font)
        lexer.setColor(QColor(palette["ed_fg"]))
        lexer.setPaper(paper)
        italic = QFont(font)
        italic.setItalic(True)
        for style in range(128):
            description = lexer.description(style)
            if not description:
                continue
            role = classify_style(description)
            lexer.setColor(QColor(palette[role]), style)
            lexer.setPaper(paper, style)
            lexer.setFont(italic if role == "comment" else font, style)

    def _setup_apis(self, lexer):
        self.api_instance = QsciAPIs(lexer)
        for word in self.language.keywords:
            self.api_instance.add(word)
        self.api_instance.prepare()

    def _get_optimal_font(self):
        return pick_editor_font(self.options.get("font_family", ""), int(self.options.get("font_size", 11)))

    def _connect_signals(self):
        self.textChanged.connect(self._on_text_content_changed)
        self.linesChanged.connect(self._update_margin_width)
        self.marginClicked.connect(self._on_margin_clicked)
        self.cursorPositionChanged.connect(self._schedule_word_highlight)
        self.selectionChanged.connect(self._schedule_word_highlight)

    def _on_text_content_changed(self):
        if not self.is_modified_flag:
            self.is_modified_flag = True
            self.content_changed_signal.emit(True)

    def mark_saved(self):
        self.is_modified_flag = False
        self.setModified(False)
        self.content_changed_signal.emit(False)

    def _on_margin_clicked(self, margin, line, _modifiers):
        if margin == 1:
            self.toggle_bookmark(line)

    # ------------------------------------------------------------- input ----

    def keyPressEvent(self, event: QKeyEvent):
        modifiers = event.modifiers()
        key = event.key()
        ctrl = Qt.KeyboardModifier.ControlModifier

        if modifiers == ctrl and key == Qt.Key.Key_D:
            self.auto_format_code()
            event.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (modifiers & ctrl) and not self.isListActive():
            super().keyPressEvent(event)
            self._handle_smart_indentation()
            return

        plain = modifiers in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier)
        if self.options.get("auto_close") and plain and not self.isListActive():
            if key == Qt.Key.Key_Backspace and self._handle_pair_backspace():
                event.accept()
                return
            text = event.text()
            if len(text) == 1 and (text in _OPENERS or text in _CLOSERS or text in _QUOTES):
                if self._handle_pair_typing(text):
                    event.accept()
                    return
        super().keyPressEvent(event)

    def _handle_pair_typing(self, ch):
        if self.hasSelectedText():
            if ch in _OPENERS or ch in _QUOTES:
                closer = _OPENERS.get(ch, ch)
                self.replaceSelectedText(ch + self.selectedText() + closer)
                return True
            return False
        line, index = self.getCursorPosition()
        text = self.text(line)
        nxt = text[index] if index < len(text) else ""
        prev = text[index - 1] if index > 0 else ""

        if ch in _CLOSERS:
            if nxt == ch:
                self.setCursorPosition(line, index + 1)
                return True
            return False
        if ch in _QUOTES:
            if nxt == ch:
                self.setCursorPosition(line, index + 1)
                return True
            if prev.isalnum() or prev in ("\\", ch) or nxt.isalnum():
                return False
            if ch == "'" and self.language.key in ("text", "markdown"):
                return False
        elif nxt and not (nxt.isspace() or nxt in ")]}.,;:"):
            return False
        closer = _OPENERS.get(ch, ch)
        self.insertAt(ch + closer, line, index)
        self.setCursorPosition(line, index + 1)
        return True

    def _handle_pair_backspace(self):
        if self.hasSelectedText():
            return False
        line, index = self.getCursorPosition()
        text = self.text(line)
        if index <= 0 or index >= len(text):
            return False
        pair = text[index - 1:index + 1]
        if pair in ("()", "[]", "{}", "''", '""', "``"):
            self.setSelection(line, index - 1, line, index + 1)
            self.removeSelectedText()
            return True
        return False

    def _handle_smart_indentation(self):
        line, index = self.getCursorPosition()
        if line <= 0:
            return
        previous = self.text(line - 1).rstrip("\r\n").rstrip()
        language = self.language
        width = self.tabWidth()
        current = self.indentation(line)
        base = self.indentation(line - 1)

        opens = (language.colon_indent and previous.endswith(":")) or \
                (language.brace_indent and previous.endswith(("{", "(", "[")))
        if opens:
            self.setIndentation(line, base + width)
            rest = self.text(line).strip()
            if rest[:1] in _CLOSERS:
                caret_pos = self._sci("SCI_GETLINEINDENTPOSITION", 2128, line)
                self._sci("SCI_GOTOPOS", 2025, caret_pos)
                _, caret_index = self.getCursorPosition()
                self.insertAt("\n", line, caret_index)
                self.setIndentation(line + 1, base)
            self._sci("SCI_GOTOPOS", 2025, self._sci("SCI_GETLINEINDENTPOSITION", 2128, line))
            return
        if language.key == "python" and re.match(r"^\s*(return|pass|break|continue|raise)\b", previous) \
                and not previous.endswith("\\") and current > 0:
            self.setIndentation(line, max(0, current - width))
            self._sci("SCI_GOTOPOS", 2025, self._sci("SCI_GETLINEINDENTPOSITION", 2128, line))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _replace_whole_text(self, new_text):
        if new_text == self.text():
            return False
        line, index = self.getCursorPosition()
        first = self.firstVisibleLine()
        self.beginUndoAction()
        try:
            self.selectAll()
            self.replaceSelectedText(new_text)
        finally:
            self.endUndoAction()
        self.setCursorPosition(min(line, max(0, self.lines() - 1)), index)
        self.setFirstVisibleLine(first)
        return True

    def auto_format_code(self):
        new_text, engine = format_source(self.text(), self.language.key)
        if self.eol == "\r\n":
            new_text = new_text.replace("\n", "\r\n")
        self._replace_whole_text(new_text)
        return engine

    def go_to_line(self, line_number):
        line_number = max(1, min(int(line_number), self.lines()))
        self.setCursorPosition(line_number - 1, 0)
        self.ensureLineVisible(line_number - 1)
        self.setFocus()

    def _selected_line_range(self):
        if self.hasSelectedText():
            line_from, _, line_to, index_to = self.getSelection()
            if index_to == 0 and line_to > line_from:
                line_to -= 1
            return line_from, line_to
        line, _ = self.getCursorPosition()
        return line, line

    def _line_body(self, line):
        return self.text(line).rstrip("\r\n")

    def toggle_comment(self):
        language = self.language
        prefix = language.comment
        block = language.block_comment
        if not prefix and not block:
            return False
        line_from, line_to = self._selected_line_range()
        bodies = [self._line_body(n) for n in range(line_from, line_to + 1)]
        active = [b for b in bodies if b.strip()]
        if not active:
            return False
        marker = prefix.rstrip() if prefix else None
        if prefix:
            uncomment = all(b.lstrip().startswith(marker) for b in active)
        else:
            uncomment = all(b.strip().startswith(block[0]) and b.strip().endswith(block[1]) for b in active)

        result = []
        indent_len = min(len(b) - len(b.lstrip()) for b in active)
        for body in bodies:
            if not body.strip():
                result.append(body)
                continue
            if prefix:
                if uncomment:
                    pos = body.index(marker)
                    after = body[pos + len(marker):]
                    if after.startswith(" ") and not prefix.endswith(" "):
                        after = after[1:]
                    result.append(body[:pos] + after)
                else:
                    gap = "" if prefix.endswith(" ") else " "
                    result.append(body[:indent_len] + prefix + gap + body[indent_len:])
            else:
                stripped = body.strip()
                lead = body[:len(body) - len(body.lstrip())]
                if uncomment:
                    inner = stripped[len(block[0]):len(stripped) - len(block[1])].strip()
                    result.append(lead + inner)
                else:
                    result.append(f"{lead}{block[0]} {stripped} {block[1]}")
        eol = "\r\n" if self.eol == "\r\n" else "\n"
        self.beginUndoAction()
        try:
            self.setSelection(line_from, 0, line_to, len(bodies[-1]))
            self.replaceSelectedText(eol.join(result))
        finally:
            self.endUndoAction()
        self.setSelection(line_from, 0, line_to, len(result[-1]))
        return True

    def duplicate_line(self):
        if self.hasSelectedText():
            self._sci("SCI_SELECTIONDUPLICATE", 2469)
        else:
            self._sci("SCI_LINEDUPLICATE", 2404)

    def delete_line(self):
        self._sci("SCI_LINEDELETE", 2338)

    def move_lines(self, up=True):
        if up:
            self._sci("SCI_MOVESELECTEDLINESUP", 2620)
        else:
            self._sci("SCI_MOVESELECTEDLINESDOWN", 2621)

    def change_case(self, upper=True):
        if not self.hasSelectedText():
            return
        self._sci("SCI_UPPERCASE" if upper else "SCI_LOWERCASE", 2342 if upper else 2341)

    def toggle_fold_all(self):
        self.foldAll(True)

    def toggle_bookmark(self, line=None):
        if line is None:
            line, _ = self.getCursorPosition()
        if self.markersAtLine(line) & (1 << MARKER_BOOKMARK):
            self.markerDelete(line, MARKER_BOOKMARK)
        else:
            self.markerAdd(line, MARKER_BOOKMARK)

    def bookmarks(self):
        found, line = [], 0
        while True:
            line = self.markerFindNext(line, 1 << MARKER_BOOKMARK)
            if line < 0:
                return found
            found.append(line)
            line += 1

    def goto_bookmark(self, forward=True):
        marks = self.bookmarks()
        if not marks:
            return False
        line, _ = self.getCursorPosition()
        if forward:
            target = next((m for m in marks if m > line), marks[0])
        else:
            target = next((m for m in reversed(marks) if m < line), marks[-1])
        self.go_to_line(target + 1)
        return True

    def clear_bookmarks(self):
        self.markerDeleteAll(MARKER_BOOKMARK)

    def set_problems(self, problems):
        self.problems = list(problems or [])
        self.markerDeleteAll(MARKER_ERROR)
        self._clear_indicator(IND_ERROR)
        for problem in self.problems:
            line = max(0, min(problem.line - 1, self.lines() - 1))
            self.markerAdd(line, MARKER_ERROR)
            body = self._line_body(line)
            start = len(body) - len(body.lstrip())
            end = len(body)
            if end <= start:
                start, end = 0, max(1, len(body))
            self.fillIndicatorRange(line, start, line, end, IND_ERROR)

    def _clear_indicator(self, indicator):
        self._sci("SCI_SETINDICATORCURRENT", 2500, indicator)
        self._sci("SCI_INDICATORCLEARRANGE", 2505, 0, self._sci("SCI_GETLENGTH", 2006))

    def find_matches(self, pattern, limit=5000):
        matches = []
        for number, raw in enumerate(self.text().split("\n")):
            body = raw.rstrip("\r")
            for match in pattern.finditer(body):
                if match.end() == match.start():
                    continue
                matches.append((number, match.start(), match.end()))
                if len(matches) >= limit:
                    return matches
        return matches

    def highlight_matches(self, pattern, limit=2000):
        self._clear_indicator(IND_MATCH)
        if pattern is None:
            return 0
        matches = self.find_matches(pattern, limit)
        for number, start, end in matches:
            self.fillIndicatorRange(number, start, number, end, IND_MATCH)
        return len(matches)

    def clear_highlights(self):
        self._clear_indicator(IND_MATCH)

    def goto_match(self, pattern, forward=True, incremental=False):
        """Select the next/previous match. Returns (current_index, total); (0, 0) when none."""
        matches = self.find_matches(pattern)
        if not matches:
            return 0, 0
        if self.hasSelectedText():
            line_from, index_from, line_to, index_to = self.getSelection()
            anchor_fwd = (line_from, index_from) if incremental else (line_to, index_to)
            anchor_back = (line_from, index_from)
        else:
            line, index = self.getCursorPosition()
            anchor_fwd = anchor_back = (line, index)
        if forward:
            position = next((i for i, m in enumerate(matches) if (m[0], m[1]) >= anchor_fwd), 0)
        else:
            position = next((i for i in range(len(matches) - 1, -1, -1)
                             if (matches[i][0], matches[i][1]) < anchor_back), len(matches) - 1)
        number, start, end = matches[position]
        self.setSelection(number, start, number, end)
        self.ensureLineVisible(number)
        return position + 1, len(matches)

    def replace_current(self, pattern, replacement, regex=False):
        if not self.hasSelectedText():
            return False
        match = pattern.fullmatch(self.selectedText())
        if match is None:
            return False
        self.replaceSelectedText(expand_replacement(match, replacement, regex))
        return True

    def replace_all_matches(self, pattern, replacement, regex=False):
        count = 0

        def substitute(match):
            nonlocal count
            if match.end() == match.start():
                return match.group(0)
            count += 1
            return expand_replacement(match, replacement, regex)

        new_text = pattern.sub(substitute, self.text())
        if count:
            self._replace_whole_text(new_text)
        return count

    def replace_all_text(self, search_text, replacement_text):
        """Plain, case-insensitive replace-all as a single undo step."""
        if not search_text:
            return 0
        return self.replace_all_matches(build_pattern(search_text), replacement_text, regex=False)

    def _schedule_word_highlight(self, *_args):
        if self.options.get("highlight_words"):
            self._word_timer.start()

    def _update_word_highlight(self):
        self._clear_indicator(IND_WORD)
        if not self.options.get("highlight_words"):
            return
        if self.hasSelectedText():
            word = self.selectedText()
        else:
            line, index = self.getCursorPosition()
            word = self.wordAtLineIndex(line, index)
        if not word or len(word) < 2 or len(word) > 80 or not re.fullmatch(r"\w+", word):
            return
        if self.length() > 2_000_000:
            return
        pattern = re.compile(rf"(?<!\w){re.escape(word)}(?!\w)")
        matches = self.find_matches(pattern, 500)
        if len(matches) < 2:
            return
        for number, start, end in matches:
            self.fillIndicatorRange(number, start, number, end, IND_WORD)

    def set_eol(self, eol, convert=False):
        mode = {
            "\r\n": QsciScintilla.EolMode.EolWindows,
            "\r": QsciScintilla.EolMode.EolMac,
        }.get(eol, QsciScintilla.EolMode.EolUnix)
        self.eol = eol if eol in ("\r\n", "\r") else "\n"
        self.setEolMode(mode)
        if convert:
            self.convertEols(mode)

    def load_text(self, text, encoding="utf-8", eol="\n"):
        """Set the initial document content without marking the editor as modified."""
        self.encoding = encoding
        self.set_eol(eol)
        self.setText(text)
        self.setModified(False)
        self.is_modified_flag = False
        self._sci("SCI_EMPTYUNDOBUFFER", 2175)
        self._update_margin_width()
