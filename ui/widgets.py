"""Reusable widgets for the Anoterra main window."""
import os
import re

from PyQt6.QtCore import QEvent, QProcess, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QKeySequence, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFontComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QSpinBox, QTabBar, QTabWidget, QTextBrowser, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.analysis import IGNORED_DIRS, parse_globs, search_in_files
from core.settings import DEFAULTS
from core.theme_data import THEMES
from core.utils import build_pattern, console_encoding, fuzzy_filter, parse_location


def _set_flag(widget, name, value):
    """Set a dynamic property and re-polish so the stylesheet picks it up."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _tool_toggle(text, tip):
    button = QToolButton()
    button.setText(text)
    button.setToolTip(tip)
    button.setCheckable(True)
    button.setAutoRaise(True)
    return button

class AnoterraTabBar(QTabBar):
    """Tab bar that closes a tab on middle click."""

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.tabCloseRequested.emit(index)
                event.accept()
                return
        super().mouseReleaseEvent(event)

class AnoterraTabWidget(QTabWidget):
    count_changed = pyqtSignal(int)
    tab_menu_requested = pyqtSignal(int, object)   

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(AnoterraTabBar(self))
        self.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._on_tab_menu)
        self.tabBar().setExpanding(False)
        self.tabBar().setDrawBase(False)

    def tabInserted(self, index):
        super().tabInserted(index)
        self.count_changed.emit(self.count())

    def tabRemoved(self, index):
        super().tabRemoved(index)
        self.count_changed.emit(self.count())

    def _on_tab_menu(self, pos):
        index = self.tabBar().tabAt(pos)
        if index >= 0:
            self.tab_menu_requested.emit(index, self.tabBar().mapToGlobal(pos))

class _FindLineEdit(QLineEdit):
    previous_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and \
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.previous_requested.emit()
            return
        super().keyPressEvent(event)


class FindReplaceBar(QFrame):
    """Inline find / replace bar shown above the editor (regex, case, whole word)."""

    closed = pyqtSignal()
    status_message = pyqtSignal(str)

    def __init__(self, get_editor, parent=None):
        super().__init__(parent)
        self.setObjectName("FindBar")
        self._get_editor = get_editor
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        row = QHBoxLayout()
        self.find_input = _FindLineEdit()
        self.find_input.setPlaceholderText("Find")
        self.find_input.setClearButtonEnabled(True)
        row.addWidget(self.find_input, 1)
        self.case_btn = _tool_toggle("Aa", "Match case")
        self.word_btn = _tool_toggle("ab", "Whole word")
        self.regex_btn = _tool_toggle(".*", "Regular expression")
        for button in (self.case_btn, self.word_btn, self.regex_btn):
            row.addWidget(button)
        self.count_label = QLabel("")
        self.count_label.setMinimumWidth(80)
        row.addWidget(self.count_label)
        self.prev_btn = QToolButton()
        self.prev_btn.setText("\u2191")
        self.prev_btn.setToolTip("Previous match (Shift+Enter)")
        self.next_btn = QToolButton()
        self.next_btn.setText("\u2193")
        self.next_btn.setToolTip("Next match (Enter / F3)")
        self.close_btn = QToolButton()
        self.close_btn.setText("\u2715")
        self.close_btn.setToolTip("Close (Esc)")
        for button in (self.prev_btn, self.next_btn, self.close_btn):
            row.addWidget(button)
        outer.addLayout(row)

        self.replace_row = QWidget()
        replace_layout = QHBoxLayout(self.replace_row)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with")
        replace_layout.addWidget(self.replace_input, 1)
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setProperty("secondary", True)
        self.replace_all_btn = QPushButton("Replace All")
        replace_layout.addWidget(self.replace_btn)
        replace_layout.addWidget(self.replace_all_btn)
        outer.addWidget(self.replace_row)
        self.replace_row.hide()

        self.find_input.textChanged.connect(lambda _text: self.refresh(select=True))
        for button in (self.case_btn, self.word_btn, self.regex_btn):
            button.toggled.connect(lambda _checked: self.refresh(select=True))
        self.find_input.returnPressed.connect(self.find_next)
        self.find_input.previous_requested.connect(self.find_previous)
        self.replace_input.returnPressed.connect(self.replace_one)
        self.next_btn.clicked.connect(self.find_next)
        self.prev_btn.clicked.connect(self.find_previous)
        self.replace_btn.clicked.connect(self.replace_one)
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.close_btn.clicked.connect(self.close_bar)
        self.hide()

    def _editor(self):
        editor = self._get_editor()
        return editor if editor is not None and hasattr(editor, "find_matches") else None

    def pattern(self):
        text = self.find_input.text()
        if not text:
            _set_flag(self.find_input, "invalid", False)
            return None
        try:
            compiled = build_pattern(text, self.case_btn.isChecked(), self.word_btn.isChecked(),
                                     self.regex_btn.isChecked())
        except (re.error, ValueError):
            _set_flag(self.find_input, "invalid", True)
            self.count_label.setText("Invalid regex")
            return None
        _set_flag(self.find_input, "invalid", False)
        return compiled

    def _show_count(self, current, total):
        if not self.find_input.text():
            self.count_label.setText("")
        elif total == 0:
            self.count_label.setText("No results")
        else:
            self.count_label.setText(f"{current} of {total}" if current else f"{total} results")

    def show_find(self, initial=""):
        self._open(initial, replace=False)

    def show_replace(self, initial=""):
        self._open(initial, replace=True)

    def _open(self, initial, replace):
        self.show()
        self.replace_row.setVisible(replace)
        if initial and "\n" not in initial:
            self.find_input.setText(initial)
        self.find_input.setFocus()
        self.find_input.selectAll()
        self.refresh(select=bool(initial))

    def refresh(self, select=False):
        editor = self._editor()
        if editor is None or not self.isVisible():
            return
        pattern = self.pattern()
        if pattern is None:
            editor.clear_highlights()
            if self.find_input.text() == "":
                self._show_count(0, 0)
            return
        total = editor.highlight_matches(pattern)
        if select and total:
            current, total = editor.goto_match(pattern, True, incremental=True)
            self.find_input.setFocus()
        else:
            current = 0
        self._show_count(current, total)

    def find_next(self):
        self._step(True)

    def find_previous(self):
        self._step(False)

    def _step(self, forward):
        editor = self._editor()
        if editor is None:
            return
        if not self.isVisible():
            self.show_find(editor.selectedText() if editor.hasSelectedText() else "")
            return
        pattern = self.pattern()
        if pattern is None:
            return
        current, total = editor.goto_match(pattern, forward)
        self._show_count(current, total)

    def replace_one(self):
        editor = self._editor()
        pattern = self.pattern()
        if editor is None or pattern is None:
            return
        editor.replace_current(pattern, self.replace_input.text(), self.regex_btn.isChecked())
        editor.highlight_matches(pattern)
        current, total = editor.goto_match(pattern, True)
        self._show_count(current, total)

    def replace_all(self):
        editor = self._editor()
        pattern = self.pattern()
        if editor is None or pattern is None:
            return
        count = editor.replace_all_matches(pattern, self.replace_input.text(), self.regex_btn.isChecked())
        editor.highlight_matches(pattern)
        self._show_count(0, len(editor.find_matches(pattern)))
        self.status_message.emit(f"Replaced {count} occurrence(s)")

    def close_bar(self):
        editor = self._editor()
        if editor is not None:
            editor.clear_highlights()
        self.hide()
        self.closed.emit()
        if editor is not None:
            editor.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
            return
        super().keyPressEvent(event)

class PaletteDialog(QDialog):
    """Fuzzy-search popup used for the command palette, quick open and go-to-symbol."""

    def __init__(self, parent, items, on_accept, placeholder="Type to search..."):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.items = list(items)           # (label, detail, payload)
        self._on_accept = on_accept
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setObjectName("PaletteFrame")
        outer.addWidget(frame)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(0)
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        layout.addWidget(self.input)
        self.list = QListWidget()
        self.list.setObjectName("PaletteList")
        self.list.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.list)
        self.resize(640, 380)

        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._accept_current)
        self.list.itemActivated.connect(lambda _item: self._accept_current())
        self.input.installEventFilter(self)
        self._filter("")

    def popup(self):
        parent = self.parentWidget()
        if parent is not None:
            geometry = parent.geometry()
            top_left = parent.mapToGlobal(parent.rect().topLeft())
            self.move(top_left.x() + (geometry.width() - self.width()) // 2, top_left.y() + 70)
        self.show()
        self.input.setFocus()

    def _filter(self, text):
        self.list.clear()
        for label, detail, payload in fuzzy_filter(text, self.items, key=lambda it: f"{it[0]} {it[1]}", limit=300):
            entry = QListWidgetItem(f"{label}      {detail}" if detail else label)
            entry.setData(Qt.ItemDataRole.UserRole, payload)
            self.list.addItem(entry)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _accept_current(self):
        item = self.list.currentItem()
        if item is None:
            return
        payload = item.data(Qt.ItemDataRole.UserRole)
        self.close()
        QTimer.singleShot(0, lambda: self._on_accept(payload))

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            step = {Qt.Key.Key_Down: 1, Qt.Key.Key_Up: -1, Qt.Key.Key_PageDown: 8, Qt.Key.Key_PageUp: -8}.get(key)
            if step is not None and self.list.count():
                row = max(0, min(self.list.count() - 1, self.list.currentRow() + step))
                self.list.setCurrentRow(row)
                return True
            if key == Qt.Key.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)

class SettingsDialog(QDialog):
    """Preferences dialog. ``values()`` returns a full settings dict."""

    PAGES = [
        ("Appearance", [
            ("theme", "Color theme", "theme", None),
            ("font_family", "Editor font", "font", None),
            ("font_size", "Font size", "int", (7, 40)),
        ]),
        ("Editor", [
            ("tab_width", "Tab width", "int", (1, 16)),
            ("use_tabs", "Indent with tab characters", "bool", None),
            ("word_wrap", "Word wrap", "bool", None),
            ("show_line_numbers", "Show line numbers", "bool", None),
            ("show_whitespace", "Show whitespace", "bool", None),
            ("show_guides", "Show indentation guides", "bool", None),
            ("show_edge", "Show right margin guide", "bool", None),
            ("edge_column", "Right margin column", "int", (40, 200)),
            ("caret_line", "Highlight current line", "bool", None),
            ("auto_close", "Auto-close brackets and quotes", "bool", None),
            ("highlight_words", "Highlight matching words", "bool", None),
            ("live_lint", "Check syntax while typing (Python / JSON)", "bool", None),
        ]),
        ("Files", [
            ("trim_trailing", "Trim trailing whitespace on save", "bool", None),
            ("final_newline", "Ensure a final newline on save", "bool", None),
            ("autosave_seconds", "Auto-save every N seconds (0 = off)", "int", (0, 3600)),
            ("restore_session", "Reopen files from last session", "bool", None),
            ("reload_external", "Reload files changed on disk", "bool", None),
        ]),
        ("Run", [
            ("python_path", "Python interpreter (empty = default)", "path", None),
            ("run_timeout", "Stop runs after N seconds (0 = never)", "int", (0, 86400)),
            ("save_before_run", "Save the file before running", "bool", None),
        ]),
    ]

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(560, 520)
        self._widgets = {}
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)
        for title, fields in self.PAGES:
            page = QWidget()
            form = QFormLayout(page)
            form.setContentsMargins(14, 14, 14, 14)
            form.setVerticalSpacing(10)
            for key, label, kind, extra in fields:
                widget = self._make_widget(kind, extra)
                self._widgets[key] = (kind, widget)
                if kind == "bool":
                    form.addRow(widget)
                    widget.setText(label)
                else:
                    form.addRow(label, widget)
            tabs.addTab(page, title)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            lambda: self._load(DEFAULTS))
        layout.addWidget(buttons)
        self._load(settings)

    def _make_widget(self, kind, extra):
        if kind == "bool":
            return QCheckBox()
        if kind == "int":
            spin = QSpinBox()
            spin.setRange(*extra)
            return spin
        if kind == "theme":
            combo = QComboBox()
            for key, palette in THEMES.items():
                combo.addItem(palette["label"], key)
            return combo
        if kind == "font":
            combo = QFontComboBox()
            combo.setFontFilters(QFontComboBox.FontFilter.MonospacedFonts)
            return combo
        if kind == "path":
            holder = QWidget()
            row = QHBoxLayout(holder)
            row.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit()
            browse = QPushButton("Browse...")
            browse.setProperty("secondary", True)
            browse.clicked.connect(lambda: self._browse(edit))
            row.addWidget(edit, 1)
            row.addWidget(browse)
            holder.edit = edit
            return holder
        return QLineEdit()

    def _browse(self, edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select interpreter", edit.text())
        if path:
            edit.setText(path)

    def _load(self, settings):
        for key, (kind, widget) in self._widgets.items():
            value = settings.get(key, DEFAULTS[key])
            if kind == "bool":
                widget.setChecked(bool(value))
            elif kind == "int":
                widget.setValue(int(value))
            elif kind == "theme":
                index = widget.findData(value)
                widget.setCurrentIndex(index if index >= 0 else 0)
            elif kind == "font":
                if value:
                    widget.setCurrentText(str(value))
                else:
                    widget.setCurrentIndex(-1)
            elif kind == "path":
                widget.edit.setText(str(value or ""))

    def values(self):
        result = {}
        for key, (kind, widget) in self._widgets.items():
            if kind == "bool":
                result[key] = widget.isChecked()
            elif kind == "int":
                result[key] = widget.value()
            elif kind == "theme":
                result[key] = widget.currentData()
            elif kind == "font":
                result[key] = widget.currentFont().family() if widget.currentIndex() >= 0 else ""
            elif kind == "path":
                result[key] = widget.edit.text().strip()
        return result

_SYMBOL_GLYPHS = {
    "class": "\u25c6", "function": "\u0192", "method": "\u0192", "heading": "\u00a7",
    "selector": "#", "table": "\u25a4", "interface": "\u25c7",
}

class OutlinePanel(QWidget):
    symbol_activated = pyqtSignal(int)      # 0-based line

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter symbols")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        layout.addWidget(self.tree, 1)
        self.empty_label = QLabel("No symbols in this file")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)
        self._symbols = []
        self.filter.textChanged.connect(self._rebuild)
        self.tree.itemActivated.connect(self._activate)
        self.tree.itemClicked.connect(self._activate)

    def set_symbols(self, symbols):
        self._symbols = list(symbols)
        self._rebuild()

    def _rebuild(self, *_args):
        needle = self.filter.text().strip().lower()
        self.tree.clear()
        parents = {}
        shown = 0
        for symbol in self._symbols:
            if needle and needle not in symbol.name.lower():
                continue
            glyph = _SYMBOL_GLYPHS.get(symbol.kind, "\u2022")
            parent = None if needle else parents.get(symbol.level - 1)
            item = QTreeWidgetItem(parent) if parent is not None else QTreeWidgetItem(self.tree)
            item.setText(0, f"{glyph}  {symbol.name}")
            item.setData(0, Qt.ItemDataRole.UserRole, symbol.line)
            item.setToolTip(0, f"{symbol.kind} \u2022 line {symbol.line + 1}")
            parents[symbol.level] = item
            for deeper in [lvl for lvl in parents if lvl > symbol.level]:
                del parents[deeper]
            shown += 1
        self.tree.expandAll()
        self.empty_label.setVisible(shown == 0)
        self.tree.setVisible(shown > 0)

    def _activate(self, item, _column=0):
        line = item.data(0, Qt.ItemDataRole.UserRole)
        if line is not None:
            self.symbol_activated.emit(int(line))


class SearchPanel(QWidget):
    """Search in files (runs incrementally on a timer so the UI never blocks)."""

    result_activated = pyqtSignal(str, int, int, int)   # path, line (1-based), start, end

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = ""
        self._generator = None
        self._groups = {}
        self._count = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search in files")
        row.addWidget(self.query, 1)
        self.case_btn = _tool_toggle("Aa", "Match case")
        self.word_btn = _tool_toggle("ab", "Whole word")
        self.regex_btn = _tool_toggle(".*", "Regular expression")
        for button in (self.case_btn, self.word_btn, self.regex_btn):
            row.addWidget(button)
        layout.addLayout(row)
        self.globs = QLineEdit()
        self.globs.setPlaceholderText("Files to include, e.g. *.py, *.js")
        layout.addWidget(self.globs)
        self.status = QLabel("")
        layout.addWidget(self.status)
        self.results = QTreeWidget()
        self.results.setHeaderHidden(True)
        self.results.setIndentation(12)
        layout.addWidget(self.results, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._tick)
        self.query.returnPressed.connect(self.start_search)
        self.globs.returnPressed.connect(self.start_search)
        self.results.itemActivated.connect(self._activate)
        self.results.itemClicked.connect(self._activate)

    def set_root(self, root):
        self.root = root

    def focus_query(self, text=""):
        if text and "\n" not in text:
            self.query.setText(text)
        self.query.setFocus()
        self.query.selectAll()

    def start_search(self):
        self._timer.stop()
        self.results.clear()
        self._groups = {}
        self._count = 0
        text = self.query.text()
        if not text or not self.root:
            self.status.setText("")
            return
        try:
            pattern = build_pattern(text, self.case_btn.isChecked(), self.word_btn.isChecked(),
                                    self.regex_btn.isChecked())
        except (re.error, ValueError) as exc:
            self.status.setText(f"Invalid pattern: {exc}")
            return
        self._generator = search_in_files(self.root, pattern, parse_globs(self.globs.text()))
        self.status.setText("Searching...")
        self._timer.start()

    def _tick(self):
        if self._generator is None:
            self._timer.stop()
            return
        for _ in range(150):
            try:
                path, line, text, start, end = next(self._generator)
            except StopIteration:
                self._generator = None
                self._timer.stop()
                self.status.setText(f"{self._count} result(s) in {len(self._groups)} file(s)")
                return
            group = self._groups.get(path)
            if group is None:
                group = QTreeWidgetItem(self.results)
                group.setText(0, os.path.relpath(path, self.root))
                group.setData(0, Qt.ItemDataRole.UserRole, None)
                self._groups[path] = group
                group.setExpanded(True)
            child = QTreeWidgetItem(group)
            child.setText(0, f"{line}:  {text.strip()[:160]}")
            child.setData(0, Qt.ItemDataRole.UserRole, (path, line, start, end))
            self._count += 1
            group.setText(0, f"{os.path.relpath(path, self.root)}  ({group.childCount()})")
        self.status.setText(f"Searching...  {self._count} result(s)")

    def _activate(self, item, _column=0):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.result_activated.emit(*data)

class OutputView(QPlainTextEdit):
    """Read-only console with colored streams and clickable ``file:line`` references."""

    location_activated = pyqtSignal(str, int, object)   # path, line, column

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OutputView")
        self.setReadOnly(True)
        self.setMaximumBlockCount(30000)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._colors = {"out": "#e6e9ef", "err": "#f2555a", "info": "#55b7c9", "ok": "#7dbb8c"}

    def set_colors(self, palette):
        self._colors = {"out": palette["fg"], "err": palette["error"], "info": palette["accent"],
                        "ok": palette["comment"]}

    def append_text(self, text, kind="out"):
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 4
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._colors.get(kind, self._colors["out"])))
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def append(self, text):
        """QTextEdit-compatible helper (adds a trailing newline)."""
        self.append_text(text if text.endswith("\n") else text + "\n", "info")

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        location = parse_location(cursor.block().text())
        if location:
            self.location_activated.emit(location[0], location[1], location[2])
            return
        super().mouseDoubleClickEvent(event)

class _HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self._cursor = 0

    def remember(self, text):
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self._cursor = len(self.history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up and self.history:
            self._cursor = max(0, self._cursor - 1)
            self.setText(self.history[self._cursor])
            return
        if event.key() == Qt.Key.Key_Down and self.history:
            self._cursor = min(len(self.history), self._cursor + 1)
            self.setText(self.history[self._cursor] if self._cursor < len(self.history) else "")
            return
        super().keyPressEvent(event)

class OutputPage(QWidget):
    stop_requested = pyqtSignal()
    input_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)
        self.status = QLabel("Ready")
        header.addWidget(self.status, 1)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("secondary", True)
        self.stop_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setProperty("secondary", True)
        header.addWidget(self.stop_btn)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)
        self.view = OutputView()
        layout.addWidget(self.view, 1)
        self.input = _HistoryLineEdit()
        self.input.setPlaceholderText("Type input for the running program and press Enter")
        self.input.setEnabled(False)
        layout.addWidget(self.input)

        self.stop_btn.clicked.connect(self.stop_requested.emit)
        self.clear_btn.clicked.connect(self.view.clear)
        self.input.returnPressed.connect(self._submit)

    def _submit(self):
        text = self.input.text()
        self.input.remember(text)
        self.input.clear()
        self.view.append_text(text + "\n", "info")
        self.input_submitted.emit(text)

    def set_running(self, running, message=None):
        self.stop_btn.setEnabled(running)
        self.input.setEnabled(running)
        if running:
            self.input.setFocus()
        if message is not None:
            self.status.setText(message)

class TerminalPage(QWidget):
    """A lightweight shell session (pipes, no PTY): good for git, pip, npm and friends."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.cwd = os.path.expanduser("~")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)
        self.status = QLabel("Terminal")
        header.addWidget(self.status, 1)
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setProperty("secondary", True)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setProperty("secondary", True)
        header.addWidget(self.restart_btn)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)
        self.view = OutputView()
        layout.addWidget(self.view, 1)
        self.input = _HistoryLineEdit()
        self.input.setPlaceholderText("Run a command and press Enter")
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._submit)
        self.clear_btn.clicked.connect(self.view.clear)
        self.restart_btn.clicked.connect(lambda: self.restart(self.cwd))

    def ensure_started(self, cwd=None):
        if cwd:
            self.cwd = cwd
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.setWorkingDirectory(self.cwd if os.path.isdir(self.cwd) else os.path.expanduser("~"))
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(lambda *_: self.view.append_text("\n[terminal exited]\n", "info"))
        if os.name == "nt":
            self.process.start("cmd.exe", [])
        else:
            self.process.start(os.environ.get("SHELL", "/bin/bash"), [])
        self.status.setText(f"Terminal \u2022 {self.cwd}")

    def restart(self, cwd=None):
        self.kill()
        self.view.append_text("[restarting terminal]\n", "info")
        self.ensure_started(cwd)

    def kill(self):
        if self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(500)

    def _read_output(self):
        data = bytes(self.process.readAllStandardOutput())
        self.view.append_text(data.decode(console_encoding(), errors="replace"), "out")

    def _submit(self):
        text = self.input.text()
        self.input.remember(text)
        self.input.clear()
        self.ensure_started()
        self.view.append_text(f"> {text}\n", "info")
        self.process.write((text + "\n").encode(console_encoding(), errors="replace"))

class ProblemsPage(QTreeWidget):
    problem_activated = pyqtSignal(int)     # 1-based line

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Problem", "Line"])
        self.setRootIsDecorated(False)
        self.setColumnWidth(0, 700)
        self.itemActivated.connect(self._activate)
        self.itemClicked.connect(self._activate)

    def set_problems(self, problems):
        self.clear()
        for problem in problems:
            item = QTreeWidgetItem([f"[{problem.severity}] {problem.message}", str(problem.line)])
            item.setData(0, Qt.ItemDataRole.UserRole, problem.line)
            self.addTopLevelItem(item)

    def _activate(self, item, _column=0):
        line = item.data(0, Qt.ItemDataRole.UserRole)
        if line:
            self.problem_activated.emit(int(line))

class AnoterraHtmlPreview(QTextBrowser):
    """Rendered preview of an HTML or Markdown editor (QTextBrowser: no JavaScript)."""

    def __init__(self, source_editor, parent=None, kind="html", base_dir=""):
        super().__init__(parent)
        self.source_editor = source_editor
        self.kind = kind
        self.base_dir = base_dir
        self.setOpenExternalLinks(True)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self.refresh)
        try:
            source_editor.textChanged.connect(self._timer.start)
        except (AttributeError, RuntimeError):
            pass

    def refresh(self):
        try:
            text = self.source_editor.text()
        except RuntimeError:        # source editor was closed
            self._timer.stop()
            return
        if self.base_dir:
            base = self.base_dir if self.base_dir.endswith(os.sep) else self.base_dir + os.sep
            self.document().setBaseUrl(QUrl.fromLocalFile(base))
        scroll = self.verticalScrollBar().value()
        if self.kind == "markdown":
            self.setMarkdown(text)
        else:
            self.setHtml(text)
        self.verticalScrollBar().setValue(scroll)

class WelcomeWidget(QWidget):
    action_requested = pyqtSignal(str)
    recent_activated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        outer = QVBoxLayout(self)
        outer.addStretch(1)
        column = QVBoxLayout()
        column.setSpacing(10)
        title = QLabel("Anoterra")
        title.setObjectName("WelcomeTitle")
        subtitle = QLabel("A fast, flexible code editor. Start something new or pick up where you left off.")
        subtitle.setObjectName("WelcomeSub")
        column.addWidget(title)
        column.addWidget(subtitle)
        column.addSpacing(8)
        for action, label, tip in (
            ("new", "New File", "Ctrl+N"), ("open", "Open File...", "Ctrl+O"),
            ("folder", "Open Folder...", "Ctrl+K Ctrl+O"), ("palette", "Command Palette", "Ctrl+Shift+P"),
            ("quick", "Go to File...", "Ctrl+P"),
        ):
            button = QPushButton(f"{label}      {tip}")
            button.setProperty("secondary", True)
            button.setMinimumHeight(34)
            button.clicked.connect(lambda _checked=False, a=action: self.action_requested.emit(a))
            column.addWidget(button)
        column.addSpacing(10)
        self.recent_label = QLabel("Recent files")
        self.recent_label.setObjectName("WelcomeSub")
        column.addWidget(self.recent_label)
        self.recent = QListWidget()
        self.recent.setMaximumHeight(190)
        self.recent.itemActivated.connect(lambda item: self.recent_activated.emit(item.data(Qt.ItemDataRole.UserRole)))
        column.addWidget(self.recent)
        holder = QWidget()
        holder.setLayout(column)
        holder.setMaximumWidth(520)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(holder)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(2)

    def set_recent(self, paths):
        self.recent.clear()
        for path in paths:
            item = QListWidgetItem(f"{os.path.basename(path)}    {os.path.dirname(path)}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent.addItem(item)
        visible = bool(paths)
        self.recent.setVisible(visible)
        self.recent_label.setVisible(visible)
