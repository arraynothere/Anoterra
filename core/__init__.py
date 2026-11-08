import os
from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciLexerCPP, QsciLexerHTML, QsciLexerCSS, QsciLexerJavaScript, QsciLexerMarkdown, QsciAPIs
from PyQt6.QtGui import QColor, QFont, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal

class AnoterraEditor(QsciScintilla):
    content_changed_signal = pyqtSignal(bool)

    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_modified_flag = False
        self._init_configurations()
        self._init_styling()
        self._init_lexer()
        self._init_signals()

    def _init_configurations(self):
        self.setUtf8(True)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(QColor("#858585"))
        self.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.setMarginsFont(FontFactory.get_editor_font())

        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)

        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#3e3e42"))
        self.setMatchedBraceForegroundColor(QColor("#4ec9b0"))

        self.setCaretForegroundColor(QColor("#aeafad"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretWidth(2)

        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColor(QColor("#1e1e1e"), QColor("#1e1e1e"))

    def _init_styling(self):
        font = FontFactory.get_editor_font()
        self.setFont(font)
        self.setColor(QColor("#d4d4d4"))
        self.setPaper(QColor("#1e1e1e"))
        self.setSelectionBackgroundColor(QColor("#264f78"))
        self.setSelectionForegroundColor(QColor("#ffffff"))

    def _init_lexer(self):
        if not self.file_path:
            self.lexer = QsciLexerPython(self)
            self._apply_lexer_theme(self.lexer)
            self.setLexer(self.lexer)
            return

        ext = os.path.splitext(self.file_path)[1].lower()
        if ext in ['.py', '.pyw']:
            self.lexer = QsciLexerPython(self)
        elif ext in ['.cpp', '.cc', '.h', '.hpp', '.c']:
            self.lexer = QsciLexerCPP(self)
        elif ext in ['.html', '.htm']:
            self.lexer = QsciLexerHTML(self)
        elif ext in ['.css', '.scss']:
            self.lexer = QsciLexerCSS(self)
        elif ext in ['.js', '.mjs', '.ts']:
            self.lexer = QsciLexerJavaScript(self)
        elif ext in ['.md', '.markdown']:
            self.lexer = QsciLexerMarkdown(self)
        else:
            self.lexer = QsciLexerPython(self)

        self._apply_lexer_theme(self.lexer)
        self.setLexer(self.lexer)

    def _apply_lexer_theme(self, lexer):
        lexer.setDefaultFont(FontFactory.get_editor_font())
        lexer.setDefaultColor(QColor("#d4d4d4"))
        lexer.setDefaultPaper(QColor("#1e1e1e"))
        
        lexer.setColor(QColor("#569cd6"), 1) 
        lexer.setColor(QColor("#ce9178"), 2) 
        lexer.setColor(QColor("#6a9955"), 3) 
        lexer.setColor(QColor("#b5cea8"), 4) 
        lexer.setColor(QColor("#4ec9b0"), 5) 
        lexer.setColor(QColor("#dcdcaa"), 6) 
        lexer.setColor(QColor("#c586c0"), 7) 

    def _init_signals(self):
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        if not self.is_modified_flag:
            self.is_modified_flag = True
            self.content_changed_signal.emit(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            self.auto_format_code()
            event.accept()
            return
        super().keyPressEvent(event)

    def auto_format_code(self):
        cursor_line, cursor_index = self.getCursorPosition()
        text = self.text()
        
        if self.file_path and self.file_path.endswith('.py'):
            lines = text.splitlines()
            formatted_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    if formatted_lines and formatted_lines[-1] != "":
                        formatted_lines.append("")
                formatted_lines.append(line)
            formatted_text = "\n".join(formatted_lines) + "\n"
            self.setText(formatted_text)
        else:
            lines = [line.rstrip() for line in text.splitlines()]
            self.setText("\n".join(lines))
        
        self.setCursorPosition(cursor_line, cursor_index)

class FontFactory:
    @staticmethod
    def get_editor_font():
        font = QFont("Cascadia Code", 11)
        if not font.exactMatch():
            font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        return font
