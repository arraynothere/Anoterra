import os
from PyQt6.Qsci import (
    QsciScintilla, QsciLexerPython, QsciLexerCPP, QsciLexerHTML,
    QsciLexerCSS, QsciLexerJavaScript, QsciLexerMarkdown, QsciAPIs
)
from PyQt6.QtGui import QColor, QFont, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal

class AnoterraEditor(QsciScintilla):
    content_changed_signal = pyqtSignal(bool)

    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_modified_flag = False
        self.lexer_instance = None
        self.api_instance = None
        
        self._configure_editor_base()
        self._configure_margins()
        self._configure_caret_and_selection()
        self._configure_folding()
        self._configure_autocomplete()
        self._init_lexer()
        self._connect_signals()

    def _configure_editor_base(self):
        self.setUtf8(True)
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#3e3e42"))
        self.setMatchedBraceForegroundColor(QColor("#4ec9b0"))
        self.setUnmatchedBraceBackgroundColor(QColor("#5a1d1d"))
        self.setUnmatchedBraceForegroundColor(QColor("#f44747"))
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 1)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _configure_margins(self):
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "00000")
        self.setMarginsForegroundColor(QColor("#858585"))
        self.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.setMarginsFont(self._get_optimal_font())

        self.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(1, 16)
        self.setMarginBackgroundColor(1, QColor("#1e1e1e"))

    def _configure_caret_and_selection(self):
        self.setCaretForegroundColor(QColor("#aeafad"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretWidth(2)
        self.setSelectionBackgroundColor(QColor("#264f78"))
        self.setSelectionForegroundColor(QColor("#ffffff"))

    def _configure_folding(self):
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColor(QColor("#1e1e1e"), QColor("#1e1e1e"))

    def _configure_autocomplete(self):
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

    def _init_lexer(self):
        font = self._get_optimal_font()
        
        if not self.file_path:
            self.lexer_instance = QsciLexerPython(self)
            self._apply_theme_to_lexer(self.lexer_instance, font)
            self.setLexer(self.lexer_instance)
            self._setup_apis(self.lexer_instance, "python")
            return

        ext = os.path.splitext(self.file_path)[1].lower()
        if ext in ['.py', '.pyw']:
            self.lexer_instance = QsciLexerPython(self)
            lang_key = "python"
        elif ext in ['.cpp', '.cc', '.h', '.hpp', '.c']:
            self.lexer_instance = QsciLexerCPP(self)
            lang_key = "cpp"
        elif ext in ['.html', '.htm']:
            self.lexer_instance = QsciLexerHTML(self)
            lang_key = "html"
        elif ext in ['.css', '.scss']:
            self.lexer_instance = QsciLexerCSS(self)
            lang_key = "css"
        elif ext in ['.js', '.mjs', '.ts']:
            self.lexer_instance = QsciLexerJavaScript(self)
            lang_key = "js"
        elif ext in ['.md', '.markdown']:
            self.lexer_instance = QsciLexerMarkdown(self)
            lang_key = "markdown"
        else:
            self.lexer_instance = QsciLexerPython(self)
            lang_key = "python"

        self._apply_theme_to_lexer(self.lexer_instance, font)
        self.setLexer(self.lexer_instance)
        self._setup_apis(self.lexer_instance, lang_key)

    def _apply_theme_to_lexer(self, lexer, font):
        lexer.setDefaultFont(font)
        lexer.setDefaultColor(QColor("#d4d4d4"))
        lexer.setDefaultPaper(QColor("#1e1e1e"))
        
        lexer.setColor(QColor("#d4d4d4"), 0)
        lexer.setColor(QColor("#569cd6"), 1)
        lexer.setColor(QColor("#ce9178"), 2)
        lexer.setColor(QColor("#6a9955"), 3)
        lexer.setColor(QColor("#b5cea8"), 4)
        lexer.setColor(QColor("#4ec9b0"), 5)
        lexer.setColor(QColor("#dcdcaa"), 6)
        lexer.setColor(QColor("#c586c0"), 7)
        lexer.setColor(QColor("#9cdcfe"), 8)
        lexer.setColor(QColor("#4fc1ff"), 9)

        lexer.setPaper(QColor("#1e1e1e"), 0)
        lexer.setPaper(QColor("#1e1e1e"), 1)
        lexer.setPaper(QColor("#1e1e1e"), 2)
        lexer.setPaper(QColor("#1e1e1e"), 3)
        lexer.setPaper(QColor("#1e1e1e"), 4)
        lexer.setPaper(QColor("#1e1e1e"), 5)
        lexer.setPaper(QColor("#1e1e1e"), 6)
        lexer.setPaper(QColor("#1e1e1e"), 7)

    def _setup_apis(self, lexer, lang_key):
        self.api_instance = QsciAPIs(lexer)
        keywords = {
            "python": ["def", "class", "import", "from", "return", "if", "elif", "else", "while", "for", "in", "try", "except", "finally", "with", "as", "lambda", "yield", "True", "False", "None", "print", "len", "range", "str", "int", "float", "list", "dict", "set"],
            "cpp": ["int", "float", "double", "char", "void", "bool", "class", "struct", "public", "private", "protected", "return", "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "std::cout", "std::cin", "include"],
            "html": ["<!DOCTYPE html>", "<html>", "<head>", "<title>", "<body>", "<div>", "<span>", "<a>", "<p>", "<ul>", "<ol>", "<li>", "<table>", "<form>", "<input>", "<button>", "class", "id", "style", "src", "href"],
            "css": ["color", "background", "background-color", "margin", "padding", "border", "font-size", "font-family", "display", "flex", "grid", "position", "width", "height", "top", "left", "right", "bottom", "text-align"],
            "js": ["function", "const", "let", "var", "return", "if", "else", "for", "while", "switch", "case", "console.log", "document.getElementById", "window", "array", "object", "async", "await", "import", "export"]
        }
        
        target_words = keywords.get(lang_key, keywords["python"])
        for word in target_words:
            self.api_instance.add(word)
        
        self.api_instance.prepare()

    def _connect_signals(self):
        self.textChanged.connect(self._on_text_content_changed)

    def _on_text_content_changed(self):
        if not self.is_modified_flag:
            self.is_modified_flag = True
            self.content_changed_signal.emit(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            self.auto_format_code()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            super().keyPressEvent(event)
            self._handle_smart_indentation()
            return

        super().keyPressEvent(event)

    def _handle_smart_indentation(self):
        line, index = self.getCursorPosition()
        if line > 0:
            prev_line_text = self.text(line - 1).rstrip()
            if prev_line_text.endswith(":"):
                current_indent = self.indentation(line - 1)
                self.setIndentation(line, current_indent + self.tabWidth())
                self.setCursorPosition(line, current_indent + self.tabWidth())

    def auto_format_code(self):
        cursor_line, cursor_index = self.getCursorPosition()
        raw_text = self.text()
        lines = raw_text.splitlines()
        
        processed_lines = []
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                processed_lines.append(stripped)
            else:
                processed_lines.append("")
        
        formatted_payload = "\n".join(processed_lines) + "\n"
        self.setText(formatted_payload)
        self.setCursorPosition(cursor_line, cursor_index)

    def _get_optimal_font(self):
        font = QFont("Cascadia Code", 11)
        if not font.exactMatch():
            font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("JetBrains Mono", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font
