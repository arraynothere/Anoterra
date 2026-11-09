import os
import shlex
import shutil
import subprocess
import sys

from PyQt6.QtCore import QFile, QFileSystemWatcher, QModelIndex, QSettings, Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QActionGroup, QDesktopServices, QFileSystemModel, QKeySequence
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QSplitter, QStackedWidget, QTabWidget, QTextBrowser, QToolBar, QToolButton,
    QTreeView, QVBoxLayout, QWidget,
)

from core.analysis import check_syntax, extract_symbols, list_workspace_files
from core.editor import AnoterraEditor
from core.languages import LANGUAGES
from core.runner import CodeRunnerEngine
from core.settings import DEFAULTS, coerce, editor_options
from core.theme_data import THEMES, get_theme
from core.utils import (
    EOL_NAMES, BinaryFileError, apply_save_transforms, format_duration, read_text_file, write_text_file,
)
from ui.themes import THEME_STYLESHEETS
from ui.widgets import (
    AnoterraHtmlPreview, AnoterraTabWidget, FindReplaceBar, OutlinePanel, OutputPage, PaletteDialog,
    ProblemsPage, SearchPanel, SettingsDialog, TerminalPage, WelcomeWidget,
)

SHORTCUTS = [
    ("File", [
        ("Ctrl+N", "New file"), ("Ctrl+Shift+N", "New HTML file"), ("Ctrl+O", "Open file(s)"),
        ("Ctrl+K, Ctrl+O", "Open folder"), ("Ctrl+P", "Go to file (quick open)"),
        ("Ctrl+S", "Save"), ("Ctrl+Shift+S", "Save all"), ("Ctrl+W", "Close tab"), ("Ctrl+,", "Settings"),
    ]),
    ("Editing", [
        ("Ctrl+D", "Format document"), ("Ctrl+/", "Toggle comment"), ("Ctrl+Shift+D", "Duplicate line"),
        ("Ctrl+Shift+K", "Delete line"), ("Alt+Up / Alt+Down", "Move line up / down"),
        ("Ctrl+Click", "Add another cursor"), ("Ctrl+Z / Ctrl+Y", "Undo / redo"),
    ]),
    ("Search & Navigate", [
        ("Ctrl+F", "Find"), ("Ctrl+H", "Find and replace"), ("F3 / Shift+F3", "Next / previous match"),
        ("Ctrl+Shift+F", "Search in files"), ("Ctrl+G", "Go to line"), ("Ctrl+Shift+O", "Go to symbol"),
        ("Ctrl+F2 / F2 / Shift+F2", "Toggle / next / previous bookmark"), ("Ctrl+Shift+P", "Command palette"),
    ]),
    ("View", [
        ("Ctrl+B", "Toggle sidebar"), ("Ctrl+J", "Toggle bottom panel"), ("Ctrl+`", "Toggle terminal"),
        ("Ctrl+= / Ctrl+- / Ctrl+0", "Zoom in / out / reset"), ("Ctrl+Shift+V", "Open preview (HTML / Markdown)"),
    ]),
    ("Run", [("F5", "Run"), ("Ctrl+F5", "Run with performance profiling"), ("Shift+F5", "Stop")]),
]

class AnoterraHelpDialog(QDialog):
    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self.setWindowTitle("Anoterra IDE - Documentation & Help")
        self.resize(760, 620)
        palette = get_theme(theme)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        sections = []
        for title, rows in SHORTCUTS:
            body = "".join(
                f"<tr><td style='padding:3px 18px 3px 0'><b>{keys}</b></td><td>{what}</td></tr>" for keys, what in rows
            )
            sections.append(f"<h3 style='color:{palette['type']}'>{title}</h3><table>{body}</table>")
        browser.setHtml(
            f"<h2 style='color:{palette['keyword']}'>Anoterra IDE</h2>"
            "<p>A fast, flexible code editor with a built-in runner, terminal, search and previews. "
            "Press <b>Ctrl+Shift+P</b> to find any command.</p>"
            + "".join(sections)
            + f"<h3 style='color:{palette['type']}'>Highlights</h3><ul>"
            "<li>Syntax highlighting for 30+ languages, switchable from the status bar</li>"
            "<li>Run Python, JavaScript, TypeScript, C, C++, Rust, Go, Java, PHP, Ruby, Lua, Perl, Shell, Batch and PowerShell</li>"
            "<li>Interactive console input, stop button, timeouts and a profiler (CPU, memory, threads)</li>"
            "<li>Click a traceback or compiler error in the console to jump to the line</li>"
            "<li>Find / replace with regex, search in files, outline and bookmarks</li>"
            "<li>Live syntax check for Python and JSON, built-in formatter (uses Black when installed)</li>"
            "<li>Embedded terminal, HTML and Markdown live preview, 5 color themes, session restore</li></ul>"
        )
        layout.addWidget(browser)

class AnoterraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._testing = os.environ.get("ANOTERRA_TESTING") == "1"
        self.setWindowTitle("Anoterra IDE")
        self.resize(1420, 900)
        self.setAcceptDrops(True)
        self.settings = QSettings("Anoterra", "Anoterra-test" if self._testing else "Anoterra")
        self.prefs = self._load_prefs()
        self.current_theme = self.prefs["theme"] if self.prefs["theme"] in THEMES else "dark"
        self.prefs["theme"] = self.current_theme
        workspace = self.settings.value("workspace", os.path.expanduser("~"))
        self.current_workspace = workspace if workspace and os.path.isdir(str(workspace)) else os.path.expanduser("~")
        self.last_search_text = ""
        try:
            self.editor_zoom = int(self.settings.value("editor_zoom", 0))
        except (TypeError, ValueError):
            self.editor_zoom = 0
        self.active_runner = None
        self.run_args = {}
        self._run_cwd = self.current_workspace
        self._quick_dialog = None
        self.setStyleSheet(THEME_STYLESHEETS[self.current_theme])

        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(450)
        self.lint_timer.timeout.connect(self._run_lint)
        self.outline_timer = QTimer(self)
        self.outline_timer.setSingleShot(True)
        self.outline_timer.setInterval(650)
        self.outline_timer.timeout.connect(self._refresh_outline)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._on_external_change)

        self._init_ui()
        self._restart_autosave()
        saved_geometry = self.settings.value("window_geometry")
        if saved_geometry:
            self.restoreGeometry(saved_geometry)
        if not self._testing and self.prefs["restore_session"]:
            self._restore_session()
        if self.editor_tabs.count() == 0:
            self._create_new_tab("Untitled.py")
        self._update_empty_state(self.editor_tabs.count())

    def _load_prefs(self):
        prefs = {}
        for key, default in DEFAULTS.items():
            stored = self.settings.value("theme" if key == "theme" else f"pref/{key}", default)
            prefs[key] = coerce(key, stored)
        return prefs

    def _save_prefs(self):
        for key, value in self.prefs.items():
            self.settings.setValue("theme" if key == "theme" else f"pref/{key}", value)

    def current_editor(self):
        widget = self.editor_tabs.currentWidget()
        return widget if isinstance(widget, AnoterraEditor) else None

    def _editors(self):
        for index in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(index)
            if isinstance(widget, AnoterraEditor):
                yield widget

    def _init_ui(self):
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # -- sidebar: explorer / search / outline
        self.sidebar = QTabWidget()
        self.sidebar.setMinimumWidth(180)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.current_workspace)
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(self.current_workspace))
        for column in range(1, 4):
            self.file_tree.setColumnHidden(column, True)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setAnimated(True)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._explorer_menu)
        self.file_tree.doubleClicked.connect(self._on_file_double_clicked)
        self.search_panel = SearchPanel()
        self.search_panel.set_root(self.current_workspace)
        self.search_panel.result_activated.connect(self._open_search_result)
        self.outline_panel = OutlinePanel()
        self.outline_panel.symbol_activated.connect(lambda line: self._goto_line_in_current(line + 1))
        self.sidebar.addTab(self.file_tree, "Explorer")
        self.sidebar.addTab(self.search_panel, "Search")
        self.sidebar.addTab(self.outline_panel, "Outline")
        self.main_splitter.addWidget(self.sidebar)
        
        self.output_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.output_splitter)

        self.editor_stack = QStackedWidget()
        self.welcome = WelcomeWidget()
        self.welcome.action_requested.connect(self._on_welcome_action)
        self.welcome.recent_activated.connect(self._open_path)
        self.editor_stack.addWidget(self.welcome)
        editor_area = QWidget()
        area_layout = QVBoxLayout(editor_area)
        area_layout.setContentsMargins(0, 0, 0, 0)
        area_layout.setSpacing(0)
        self.editor_tabs = AnoterraTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_tab)
        self.editor_tabs.currentChanged.connect(self._on_current_tab_changed)
        self.editor_tabs.count_changed.connect(self._update_empty_state)
        self.editor_tabs.tab_menu_requested.connect(self._tab_menu)
        self.find_bar = FindReplaceBar(self.current_editor)
        self.find_bar.status_message.connect(lambda text: self.statusBar().showMessage(text, 3000))
        area_layout.addWidget(self.find_bar)
        area_layout.addWidget(self.editor_tabs, 1)
        self.editor_stack.addWidget(editor_area)
        self.output_splitter.addWidget(self.editor_stack)
        
        self.bottom_tabs = QTabWidget()
        self.output_panel = self.bottom_tabs
        self.output_page = OutputPage()
        self.console_output = self.output_page.view
        self.output_page.stop_requested.connect(self._stop_execution)
        self.output_page.input_submitted.connect(self._send_program_input)
        self.output_page.view.location_activated.connect(self._open_location)
        self.problems_page = ProblemsPage()
        self.problems_page.problem_activated.connect(self._goto_line_in_current)
        self.terminal_page = TerminalPage()
        self.terminal_page.view.location_activated.connect(self._open_location)
        self.bottom_tabs.addTab(self.output_page, "Output")
        self.bottom_tabs.addTab(self.problems_page, "Problems")
        self.bottom_tabs.addTab(self.terminal_page, "Terminal")
        self.bottom_tabs.currentChanged.connect(self._on_bottom_tab_changed)
        self.output_splitter.addWidget(self.bottom_tabs)
        self._apply_output_colors()

        self.main_splitter.setSizes([280, 1140])
        self.output_splitter.setSizes([650, 230])
        self.main_splitter.setStretchFactor(1, 1)
        saved_main = self.settings.value("main_splitter_sizes")
        saved_output = self.settings.value("output_splitter_sizes")
        try:
            if saved_main:
                self.main_splitter.setSizes([int(size) for size in saved_main])
            if saved_output:
                self.output_splitter.setSizes([int(size) for size in saved_output])
        except (TypeError, ValueError):
            pass

        self._init_menus_and_toolbars()
        self._init_status_bar()
        self.welcome.set_recent(self._recent_files())

    def _act(self, menu, text, slot, shortcut=None, checkable=False, checked=False):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
            action.toggled.connect(slot)
        else:
            action.triggered.connect(lambda _checked=False: slot())
        menu.addAction(action)
        return action

    def _menu_item(self, menu, text, slot):
        action = QAction(text, menu)
        action.triggered.connect(lambda _checked=False: slot())
        menu.addAction(action)
        return action

    def _with_editor(self, function):
        editor = self.current_editor()
        if editor is not None:
            function(editor)

    def _init_menus_and_toolbars(self):
        menubar = self.menuBar()
        S = QKeySequence.StandardKey

        file_menu = menubar.addMenu("&File")
        self._act(file_menu, "New File", lambda: self._create_new_tab("Untitled.py"), S.New)
        self._act(file_menu, "New HTML File", lambda: self._create_new_tab("Untitled.html"), "Ctrl+Shift+N")
        self._act(file_menu, "Open File...", self._open_file_dialog, S.Open)
        self._act(file_menu, "Open Workspace Folder...", self._open_workspace_folder, "Ctrl+K, Ctrl+O")
        self.recent_menu = file_menu.addMenu("Open Recent")
        self.recent_menu.aboutToShow.connect(self._fill_recent_menu)
        self._act(file_menu, "Go to File...", self._show_quick_open, "Ctrl+P")
        file_menu.addSeparator()
        self._act(file_menu, "Save", self._save_active_file, S.Save)
        self._act(file_menu, "Save As...", self._save_active_as, "Ctrl+Alt+S")
        self._act(file_menu, "Save All", self._save_all_files, "Ctrl+Shift+S")
        self._act(file_menu, "Reload from Disk", self._reload_active)
        file_menu.addSeparator()
        self._act(file_menu, "Close Tab", lambda: self._close_tab(self.editor_tabs.currentIndex()), "Ctrl+W")
        self._act(file_menu, "Close All Tabs", self._close_all_tabs)
        file_menu.addSeparator()
        self._act(file_menu, "Settings...", self._open_settings, "Ctrl+,")
        self._act(file_menu, "Exit", self.close, "Ctrl+Q")

        edit_menu = menubar.addMenu("&Edit")
        self._act(edit_menu, "Undo", lambda: self._with_editor(lambda e: e.undo()), S.Undo)
        self._act(edit_menu, "Redo", lambda: self._with_editor(lambda e: e.redo()), S.Redo)
        edit_menu.addSeparator()
        self._act(edit_menu, "Find...", self._trigger_find, S.Find)
        self._act(edit_menu, "Find Next", self._find_next, "F3")
        self._act(edit_menu, "Find Previous", self._find_previous, "Shift+F3")
        self._act(edit_menu, "Replace...", self._trigger_replace, S.Replace)
        self._act(edit_menu, "Find in Files...", self._find_in_files, "Ctrl+Shift+F")
        edit_menu.addSeparator()
        self._act(edit_menu, "Toggle Comment", lambda: self._with_editor(lambda e: e.toggle_comment()), "Ctrl+/")
        self._act(edit_menu, "Duplicate Line", lambda: self._with_editor(lambda e: e.duplicate_line()), "Ctrl+Shift+D")
        self._act(edit_menu, "Delete Line", lambda: self._with_editor(lambda e: e.delete_line()), "Ctrl+Shift+K")
        self._act(edit_menu, "Move Line Up", lambda: self._with_editor(lambda e: e.move_lines(True)), "Alt+Up")
        self._act(edit_menu, "Move Line Down", lambda: self._with_editor(lambda e: e.move_lines(False)), "Alt+Down")
        self._act(edit_menu, "Transform to Uppercase", lambda: self._with_editor(lambda e: e.change_case(True)), "Ctrl+Shift+U")
        self._act(edit_menu, "Transform to Lowercase", lambda: self._with_editor(lambda e: e.change_case(False)), "Ctrl+Alt+U")
        self._act(edit_menu, "Format Document (Ctrl+D)", self._trigger_auto_format)

        selection_menu = menubar.addMenu("&Selection")
        self._act(selection_menu, "Select All", self._trigger_select_all, S.SelectAll)

        view_menu = menubar.addMenu("&View")
        self._act(view_menu, "Command Palette...", self._show_command_palette, "Ctrl+Shift+P")
        view_menu.addSeparator()
        self._act(view_menu, "Toggle Sidebar", self._toggle_file_tree, "Ctrl+B")
        self._act(view_menu, "Show Explorer", lambda: self._show_sidebar(0), "Ctrl+Shift+E")
        self._act(view_menu, "Show Outline", lambda: self._show_sidebar(2))
        self._act(view_menu, "Toggle Bottom Panel", self._toggle_console_panel, "Ctrl+J")
        self._act(view_menu, "Show Output", lambda: self._show_bottom(0))
        self._act(view_menu, "Show Problems", lambda: self._show_bottom(1))
        self._act(view_menu, "Toggle Terminal", self._toggle_terminal, "Ctrl+`")
        self._act(view_menu, "Open Preview (HTML / Markdown)", self._open_preview_for_current, "Ctrl+Shift+V")
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions = {}
        for key, palette in THEMES.items():
            action = QAction(palette["label"], self)
            action.setCheckable(True)
            action.setChecked(key == self.current_theme)
            action.triggered.connect(lambda _checked=False, name=key: self._set_theme(name))
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[key] = action
        view_menu.addSeparator()
        self.word_wrap_action = self._act(view_menu, "Word Wrap", self._toggle_word_wrap,
                                          checkable=True, checked=self.prefs["word_wrap"])
        self.whitespace_action = self._act(view_menu, "Show Whitespace", self._toggle_whitespace,
                                           checkable=True, checked=self.prefs["show_whitespace"])
        self._act(view_menu, "Fold / Unfold All", lambda: self._with_editor(lambda e: e.toggle_fold_all()))
        self._act(view_menu, "Zoom In", self._zoom_in, "Ctrl+=")
        self._act(view_menu, "Zoom Out", self._zoom_out, "Ctrl+-")
        self._act(view_menu, "Reset Editor Zoom", self._reset_zoom, "Ctrl+0")

        goto_menu = menubar.addMenu("&Goto")
        self._act(goto_menu, "Goto Line...", self._trigger_goto_line, "Ctrl+G")
        self._act(goto_menu, "Go to Symbol...", self._show_symbol_palette, "Ctrl+Shift+O")
        goto_menu.addSeparator()
        self._act(goto_menu, "Toggle Bookmark", lambda: self._with_editor(lambda e: e.toggle_bookmark()), "Ctrl+F2")
        self._act(goto_menu, "Next Bookmark", lambda: self._with_editor(lambda e: e.goto_bookmark(True)), "F2")
        self._act(goto_menu, "Previous Bookmark", lambda: self._with_editor(lambda e: e.goto_bookmark(False)), "Shift+F2")
        self._act(goto_menu, "Clear Bookmarks", lambda: self._with_editor(lambda e: e.clear_bookmarks()))
        goto_menu.addSeparator()
        self._act(goto_menu, "Next Tab", lambda: self._cycle_tab(1), "Ctrl+PgDown")
        self._act(goto_menu, "Previous Tab", lambda: self._cycle_tab(-1), "Ctrl+PgUp")

        run_menu = menubar.addMenu("&Execution")
        self._act(run_menu, "Run Script", lambda: self._execute_code("run"), "F5")
        self._act(run_menu, "Run & Debug", lambda: self._execute_code("debug"), "Ctrl+F5")
        self._act(run_menu, "Run with Arguments...", self._run_with_arguments)
        self._act(run_menu, "Stop", self._stop_execution, "Shift+F5")

        help_menu = menubar.addMenu("&Help")
        self._act(help_menu, "Documentation & Shortcuts", self._open_help_dialog, "F1")
        self._act(help_menu, "About Anoterra", self._show_about)

        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        for text, slot, tip in (
            ("\u25b6 Run", lambda: self._execute_code("run"), "Run (F5)"),
            ("\u25c9 Debug", lambda: self._execute_code("debug"), "Run with profiling (Ctrl+F5)"),
            ("\u25a0 Stop", self._stop_execution, "Stop (Shift+F5)"),
        ):
            action = QAction(text, self)
            action.setToolTip(tip)
            action.triggered.connect(lambda _checked=False, s=slot: s())
            self.toolbar.addAction(action)
        self.toolbar.addSeparator()
        for text, slot, tip in (
            ("Format", self._trigger_auto_format, "Format document (Ctrl+D)"),
            ("Find", self._trigger_find, "Find (Ctrl+F)"),
            ("Search Files", self._find_in_files, "Search in files (Ctrl+Shift+F)"),
            ("Commands", self._show_command_palette, "Command palette (Ctrl+Shift+P)"),
        ):
            action = QAction(text, self)
            action.setToolTip(tip)
            action.triggered.connect(lambda _checked=False, s=slot: s())
            self.toolbar.addAction(action)

    def _init_status_bar(self):
        bar = self.statusBar()
        self.cursor_status = QLabel("Ln 1, Col 1")
        self.cursor_status.setMinimumWidth(150)
        self.indent_button = self._status_button("Spaces: 4", "Indentation")
        self.encoding_label = QLabel("UTF-8")
        self.eol_button = self._status_button("LF", "End of line sequence")
        self.language_button = self._status_button("Python", "Language mode")

        indent_menu = QMenu(self)
        for label, tabs, width in (("Spaces: 2", False, 2), ("Spaces: 4", False, 4), ("Spaces: 8", False, 8),
                                   ("Tabs (width 4)", True, 4), ("Tabs (width 8)", True, 8)):
            self._menu_item(indent_menu, label, lambda t=tabs, w=width: self._set_indent(t, w))
        self.indent_button.setMenu(indent_menu)
        eol_menu = QMenu(self)
        for label, eol in (("LF  (Unix / macOS)", "\n"), ("CRLF  (Windows)", "\r\n"), ("CR  (classic Mac)", "\r")):
            self._menu_item(eol_menu, label, lambda e=eol: self._set_eol(e))
        self.eol_button.setMenu(eol_menu)
        language_menu = QMenu(self)
        self._menu_item(language_menu, "Auto Detect", lambda: self._set_language(None))
        language_menu.addSeparator()
        for language in sorted(LANGUAGES, key=lambda lang: lang.name.lower()):
            self._menu_item(language_menu, language.name, lambda key=language.key: self._set_language(key))
        self.language_button.setMenu(language_menu)

        for widget in (self.cursor_status, self.indent_button, self.encoding_label, self.eol_button, self.language_button):
            bar.addPermanentWidget(widget)
        bar.showMessage("Anoterra IDE ready")

    @staticmethod
    def _status_button(text, tip):
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tip)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        return button

    # ---------------------------------------------------------------- tabs ----

    def _create_new_tab(self, title, file_path=None, content="", encoding="utf-8", eol=None):
        editor = AnoterraEditor(file_path=file_path, language_hint=title)
        editor.apply_options(editor_options(self.prefs))
        editor.set_theme(self.current_theme)
        editor.zoomTo(self.editor_zoom)
        if not content and not file_path and os.path.splitext(title)[1].lower() in (".html", ".htm"):
            content = (
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>My Anoterra Page</title>\n"
                "</head>\n"
                "<body>\n"
                "    <h1>Hello from Anoterra!</h1>\n"
                "    <p>Edit this page, then press F5 to preview it.</p>\n"
                "</body>\n"
                "</html>\n"
            )
            eol = "\n"
        if content:
            editor.load_text(content, encoding, eol or ("\r\n" if "\r\n" in content else "\n"))
        if file_path and os.path.exists(file_path):
            editor.disk_mtime = os.path.getmtime(file_path)
            self._watch(file_path)
        editor.content_changed_signal.connect(
            lambda modified, current=editor: self._update_tab_modified_state(current, modified)
        )
        editor.content_changed_signal.connect(lambda _m: self._schedule_analysis())
        editor.textChanged.connect(self._schedule_analysis)
        editor.cursorPositionChanged.connect(self._update_cursor_status)
        editor.selectionChanged.connect(self._update_cursor_status)
        editor.files_dropped.connect(self._open_paths)
        index = self.editor_tabs.addTab(editor, title)
        if file_path:
            self.editor_tabs.setTabToolTip(index, file_path)
        self.editor_tabs.setCurrentIndex(index)
        self._update_cursor_status()
        self._schedule_analysis()
        return editor

    def _update_tab_modified_state(self, editor, modified):
        index = self.editor_tabs.indexOf(editor)
        if index < 0:
            return
        title = self.editor_tabs.tabText(index)
        if title.endswith(" *"):
            title = title[:-2]
        self.editor_tabs.setTabText(index, f"{title} *" if modified else title)
        self._update_window_title()

    def _update_window_title(self):
        editor = self.current_editor()
        if editor is None:
            self.setWindowTitle("Anoterra IDE")
            return
        name = os.path.basename(editor.file_path) if editor.file_path else \
            self.editor_tabs.tabText(self.editor_tabs.currentIndex()).removesuffix(" *")
        mark = " \u2022" if editor.is_modified_flag else ""
        self.setWindowTitle(f"{name}{mark} \u2014 Anoterra IDE")

    def _update_empty_state(self, count):
        self.editor_stack.setCurrentIndex(1 if count else 0)
        if count == 0:
            self.find_bar.hide()
            self.welcome.set_recent(self._recent_files())
            self.setWindowTitle("Anoterra IDE")
            self.outline_panel.set_symbols([])
            self.problems_page.set_problems([])

    def _on_current_tab_changed(self, _index=-1):
        self._update_cursor_status()
        self._update_window_title()
        self._schedule_analysis(immediate=True)
        if self.find_bar.isVisible():
            self.find_bar.refresh()

    def _cycle_tab(self, step):
        count = self.editor_tabs.count()
        if count:
            self.editor_tabs.setCurrentIndex((self.editor_tabs.currentIndex() + step) % count)

    def _close_tab(self, index):
        if index < 0:
            return
        widget = self.editor_tabs.widget(index)
        if isinstance(widget, AnoterraEditor) and widget.is_modified_flag:
            self.editor_tabs.setCurrentIndex(index)
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"Do you want to save changes to {self.editor_tabs.tabText(index).removesuffix(' *')}?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                if not self._save_editor(widget):
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        self._remove_tab(index)

    def _remove_tab(self, index):
        widget = self.editor_tabs.widget(index)
        path = widget.file_path if isinstance(widget, AnoterraEditor) else None
        self.editor_tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()
        if path and not any(e.file_path == path for e in self._editors()):
            self.watcher.removePath(path)

    def _close_all_tabs(self):
        for index in range(self.editor_tabs.count() - 1, -1, -1):
            self._close_tab(index)

    def _tab_menu(self, index, global_pos):
        widget = self.editor_tabs.widget(index)
        path = widget.file_path if isinstance(widget, AnoterraEditor) else None
        menu = QMenu(self)
        self._menu_item(menu, "Close", lambda: self._close_tab(index))
        self._menu_item(menu, "Close Others", lambda: self._close_others(index))
        self._menu_item(menu, "Close to the Right", lambda: self._close_right(index))
        self._menu_item(menu, "Close All", self._close_all_tabs)
        if path:
            menu.addSeparator()
            self._menu_item(menu, "Copy Path", lambda: QApplication.clipboard().setText(path))
            self._menu_item(menu, "Reveal in File Manager", lambda: self._reveal(path))
        menu.exec(global_pos)

    def _close_others(self, keep):
        keep_widget = self.editor_tabs.widget(keep)
        for index in range(self.editor_tabs.count() - 1, -1, -1):
            if self.editor_tabs.widget(index) is not keep_widget:
                self._close_tab(index)

    def _close_right(self, index):
        for i in range(self.editor_tabs.count() - 1, index, -1):
            self._close_tab(i)

    def _update_cursor_status(self, *args):
        widget = self.editor_tabs.currentWidget()
        if isinstance(widget, AnoterraEditor):
            line, column = widget.getCursorPosition()
            text = f"Ln {line + 1}, Col {column + 1}"
            if widget.hasSelectedText():
                text += f"  ({len(widget.selectedText())} selected)"
            self.cursor_status.setText(text)
            self.word_wrap_action.blockSignals(True)
            self.word_wrap_action.setChecked(widget.wrapMode() != QsciScintilla.WrapMode.WrapNone)
            self.word_wrap_action.blockSignals(False)
            self.language_button.setText(widget.language.name)
            self.eol_button.setText(EOL_NAMES.get(widget.eol, "LF"))
            self.encoding_label.setText(widget.encoding.upper().replace("UTF-8-SIG", "UTF-8 BOM"))
            opts = widget.options
            self.indent_button.setText(f"{'Tabs' if opts['use_tabs'] else 'Spaces'}: {opts['tab_width']}")
        elif isinstance(widget, AnoterraHtmlPreview):
            self.cursor_status.setText("Preview")
        else:
            self.cursor_status.setText("")

    def _set_indent(self, use_tabs, width):
        self._with_editor(lambda e: e.apply_options({"use_tabs": use_tabs, "tab_width": width}))
        self._update_cursor_status()

    def _set_eol(self, eol):
        self._with_editor(lambda e: e.set_eol(eol, convert=True))
        self._update_cursor_status()

    def _set_language(self, key):
        editor = self.current_editor()
        if editor is not None:
            editor.set_language(key)
            self._update_cursor_status()
            self._schedule_analysis(immediate=True)

    def _schedule_analysis(self, immediate=False):
        if immediate:
            self._run_lint()
            self._refresh_outline()
            return
        self.lint_timer.start()
        self.outline_timer.start()

    def _run_lint(self):
        editor = self.current_editor()
        if editor is None:
            return
        problems = []
        if self.prefs["live_lint"] and editor.language.key in ("python", "json") and editor.length() < 1_500_000:
            problems = check_syntax(editor.text(), editor.language.key)
        editor.set_problems(problems)
        self.problems_page.set_problems(problems)
        self.bottom_tabs.setTabText(1, f"Problems ({len(problems)})" if problems else "Problems")

    def _refresh_outline(self):
        editor = self.current_editor()
        if editor is None or editor.length() > 1_500_000:
            self.outline_panel.set_symbols([])
            return
        self.outline_panel.set_symbols(extract_symbols(editor.text(), editor.language.key))

    def _goto_line_in_current(self, line_number):
        editor = self.current_editor()
        if editor is not None:
            editor.go_to_line(line_number)

    def _recent_files(self):
        value = self.settings.value("recent_files", [])
        if isinstance(value, str):
            value = [value] if value else []
        return [p for p in (value or []) if isinstance(p, str) and os.path.exists(p)][:10]

    def _remember_recent(self, path):
        recent = [p for p in self._recent_files() if os.path.normcase(p) != os.path.normcase(path)]
        recent.insert(0, path)
        self.settings.setValue("recent_files", recent[:10])

    def _fill_recent_menu(self):
        self.recent_menu.clear()
        recent = self._recent_files()
        if not recent:
            self.recent_menu.addAction("(empty)").setEnabled(False)
        for path in recent:
            self._menu_item(self.recent_menu, path, lambda p=path: self._open_path(p))

    def _find_open_editor(self, path):
        target = os.path.normcase(os.path.abspath(path))
        for editor in self._editors():
            if editor.file_path and os.path.normcase(os.path.abspath(editor.file_path)) == target:
                return editor
        return None

    def _open_path(self, path, line=None):
        path = os.path.abspath(path)
        if os.path.isdir(path):
            self._set_workspace(path)
            return None
        existing = self._find_open_editor(path)
        if existing is not None:
            self.editor_tabs.setCurrentWidget(existing)
            if line:
                existing.go_to_line(line)
            return existing
        try:
            loaded = read_text_file(path)
        except BinaryFileError as exc:
            QMessageBox.warning(self, "Cannot open file", f"{os.path.basename(path)}\n\n{exc}")
            return None
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{exc}")
            return None
        pristine = None
        if self.editor_tabs.count() == 1:
            first = self.current_editor()
            if first is not None and not first.file_path and not first.is_modified_flag and not first.text():
                pristine = self.editor_tabs.currentIndex()
        editor = self._create_new_tab(os.path.basename(path), file_path=path, content=loaded.text,
                                      encoding=loaded.encoding, eol=loaded.eol)
        if not loaded.text:
            editor.load_text("", loaded.encoding, loaded.eol)
        if pristine is not None:
            self._remove_tab(pristine)
        self._remember_recent(path)
        if line:
            editor.go_to_line(line)
        return editor

    def _open_paths(self, paths):
        for path in paths:
            self._open_path(path)

    def _on_file_double_clicked(self, index: QModelIndex):
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            self._open_path(path)

    def _open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open File", self.current_workspace)
        self._open_paths(paths)

    def _open_workspace_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Workspace Folder", self.current_workspace)
        if folder:
            self._set_workspace(folder)

    def _set_workspace(self, folder):
        folder = os.path.abspath(folder)
        self.current_workspace = folder
        self.file_model.setRootPath(folder)
        self.file_tree.setRootIndex(self.file_model.index(folder))
        self.search_panel.set_root(folder)
        self.terminal_page.cwd = folder
        self.statusBar().showMessage(f"Workspace loaded: {folder}", 4000)

    def _open_search_result(self, path, line, start, end):
        editor = self._open_path(path, line)
        if editor is not None:
            editor.setSelection(line - 1, start, line - 1, end)

    def _open_location(self, path, line, _column=None):
        candidates = [path] if os.path.isabs(path) else [
            os.path.join(self._run_cwd, path), os.path.join(self.current_workspace, path)
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                self._open_path(candidate, line)
                return
        self.statusBar().showMessage(f"Cannot find {path}", 3000)

    def _on_welcome_action(self, action):
        {
            "new": lambda: self._create_new_tab("Untitled.py"),
            "open": self._open_file_dialog,
            "folder": self._open_workspace_folder,
            "palette": self._show_command_palette,
            "quick": self._show_quick_open,
        }[action]()

    # ---------------------------------------------------------------- saving ----

    def _save_editor(self, editor, force_dialog=False):
        if not isinstance(editor, AnoterraEditor):
            return False
        index = self.editor_tabs.indexOf(editor)
        if force_dialog or not editor.file_path:
            title = self.editor_tabs.tabText(index).removesuffix(" *") if index >= 0 else "Untitled.py"
            default_path = editor.file_path or os.path.join(self.current_workspace, title)
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_path)
            if not file_path:
                return False
            if editor.file_path and editor.file_path != file_path:
                self.watcher.removePath(editor.file_path)
            editor.set_file_path(file_path)
            self._update_cursor_status()
        text = editor.text()
        cleaned = apply_save_transforms(text, self.prefs["trim_trailing"], self.prefs["final_newline"], editor.eol)
        if cleaned != text:
            editor._replace_whole_text(cleaned)
        try:
            write_text_file(editor.file_path, editor.text(), editor.encoding)
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{exc}")
            return False
        editor.disk_mtime = os.path.getmtime(editor.file_path)
        self._watch(editor.file_path)
        if index >= 0:
            self.editor_tabs.setTabText(index, os.path.basename(editor.file_path))
            self.editor_tabs.setTabToolTip(index, editor.file_path)
        editor.mark_saved()
        self._remember_recent(editor.file_path)
        self._update_window_title()
        self.statusBar().showMessage(f"Saved: {editor.file_path}", 3000)
        return True

    def _save_active_file(self):
        return self._save_editor(self.current_editor())

    def _save_active_as(self):
        return self._save_editor(self.current_editor(), force_dialog=True)

    def _save_all_files(self):
        saved_count = 0
        for editor in list(self._editors()):
            if not editor.file_path and not editor.is_modified_flag:
                continue
            needs_write = editor.is_modified_flag or not editor.file_path or not os.path.exists(editor.file_path)
            if not needs_write:
                continue
            if not self._save_editor(editor):
                return saved_count
            saved_count += 1
        self.statusBar().showMessage(f"Saved {saved_count} file(s)", 3000)
        return saved_count

    def _autosave(self):
        for editor in self._editors():
            if editor.file_path and editor.is_modified_flag:
                self._save_editor(editor)

    def _restart_autosave(self):
        seconds = self.prefs["autosave_seconds"]
        if seconds > 0:
            self.autosave_timer.start(seconds * 1000)
        else:
            self.autosave_timer.stop()

    # ------------------------------------------------- external file changes ----

    def _watch(self, path):
        if path and os.path.exists(path) and path not in self.watcher.files():
            self.watcher.addPath(path)

    def _on_external_change(self, path):
        QTimer.singleShot(200, lambda: self._handle_external_change(path))

    def _handle_external_change(self, path):
        if not os.path.exists(path):
            return
        self._watch(path)
        if not self.prefs["reload_external"]:
            return
        editor = self._find_open_editor(path)
        if editor is None:
            return
        mtime = os.path.getmtime(path)
        if editor.disk_mtime is not None and abs(mtime - editor.disk_mtime) < 0.01:
            return
        if editor.is_modified_flag:
            if self._testing:
                return
            answer = QMessageBox.question(
                self, "File changed on disk",
                f"{os.path.basename(path)} was changed outside Anoterra.\nReload it and lose your unsaved edits?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                editor.disk_mtime = mtime
                return
        self._reload_editor(editor)

    def _reload_editor(self, editor):
        if not editor.file_path:
            return
        try:
            loaded = read_text_file(editor.file_path)
        except (OSError, BinaryFileError) as exc:
            self.statusBar().showMessage(f"Reload failed: {exc}", 4000)
            return
        line, index = editor.getCursorPosition()
        first = editor.firstVisibleLine()
        editor.load_text(loaded.text, loaded.encoding, loaded.eol)
        editor.setCursorPosition(min(line, max(0, editor.lines() - 1)), index)
        editor.setFirstVisibleLine(first)
        editor.disk_mtime = os.path.getmtime(editor.file_path)
        editor.mark_saved()
        self.statusBar().showMessage(f"Reloaded {os.path.basename(editor.file_path)} from disk", 3000)

    def _reload_active(self):
        editor = self.current_editor()
        if editor is not None:
            self._reload_editor(editor)

    def _explorer_menu(self, pos):
        index = self.file_tree.indexAt(pos)
        path = self.file_model.filePath(index) if index.isValid() else self.current_workspace
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        menu = QMenu(self)
        if index.isValid() and os.path.isfile(path):
            self._menu_item(menu, "Open", lambda: self._open_path(path))
            menu.addSeparator()
        self._menu_item(menu, "New File...", lambda: self._new_file_in(folder))
        self._menu_item(menu, "New Folder...", lambda: self._new_folder_in(folder))
        if index.isValid():
            menu.addSeparator()
            self._menu_item(menu, "Rename...", lambda: self._rename_path(path))
            self._menu_item(menu, "Delete", lambda: self._delete_path(path))
            menu.addSeparator()
            self._menu_item(menu, "Copy Path", lambda: QApplication.clipboard().setText(path))
            self._menu_item(menu, "Copy Relative Path", lambda: QApplication.clipboard().setText(
                os.path.relpath(path, self.current_workspace)))
            self._menu_item(menu, "Reveal in File Manager", lambda: self._reveal(path))
            if os.path.isdir(path):
                self._menu_item(menu, "Set as Workspace Root", lambda: self._set_workspace(path))
        menu.exec(self.file_tree.viewport().mapToGlobal(pos))

    def _new_file_in(self, folder):
        name, accepted = QInputDialog.getText(self, "New File", "File name:")
        if not accepted or not name.strip():
            return
        target = os.path.join(folder, name.strip())
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "x", encoding="utf-8"):
                pass
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not create file:\n{exc}")
            return
        self._open_path(target)

    def _new_folder_in(self, folder):
        name, accepted = QInputDialog.getText(self, "New Folder", "Folder name:")
        if accepted and name.strip():
            try:
                os.makedirs(os.path.join(folder, name.strip()), exist_ok=False)
            except OSError as exc:
                QMessageBox.critical(self, "Error", f"Could not create folder:\n{exc}")

    def _rename_path(self, path):
        name, accepted = QInputDialog.getText(self, "Rename", "New name:", QLineEdit.EchoMode.Normal,
                                              os.path.basename(path))
        if not accepted or not name.strip() or name == os.path.basename(path):
            return
        target = os.path.join(os.path.dirname(path), name.strip())
        try:
            os.rename(path, target)
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"Could not rename:\n{exc}")
            return
        for editor in self._editors():
            if editor.file_path and os.path.normcase(editor.file_path).startswith(os.path.normcase(path)):
                new_path = target + editor.file_path[len(path):]
                self.watcher.removePath(editor.file_path)
                editor.set_file_path(new_path)
                index = self.editor_tabs.indexOf(editor)
                self.editor_tabs.setTabText(index, os.path.basename(new_path) + (" *" if editor.is_modified_flag else ""))
                self._watch(new_path)

    def _delete_path(self, path):
        answer = QMessageBox.question(self, "Delete", f"Move '{os.path.basename(path)}' to the trash?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        if not QFile.moveToTrash(path):
            try:
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
            except OSError as exc:
                QMessageBox.critical(self, "Error", f"Could not delete:\n{exc}")
                return
        for index in range(self.editor_tabs.count() - 1, -1, -1):
            widget = self.editor_tabs.widget(index)
            if isinstance(widget, AnoterraEditor) and widget.file_path and \
                    os.path.normcase(widget.file_path).startswith(os.path.normcase(path)):
                self._remove_tab(index)

    @staticmethod
    def _reveal(path):
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                folder = path if os.path.isdir(path) else os.path.dirname(path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        except OSError:
            pass

    def _show_popup(self, items, on_accept, placeholder):
        self._quick_dialog = PaletteDialog(self, items, on_accept, placeholder)
        self._quick_dialog.popup()

    def _show_command_palette(self):
        items = []

        def walk(menu, prefix):
            for action in menu.actions():
                if action.isSeparator():
                    continue
                label = action.text().replace("&", "")
                if action.menu() is not None:
                    walk(action.menu(), f"{prefix}{label}: ")
                elif label != "(empty)":
                    items.append((f"{prefix}{label}", action.shortcut().toString(), action))

        for top in self.menuBar().actions():
            if top.menu() is not None:
                walk(top.menu(), f"{top.text().replace('&', '')}: ")
        self._show_popup(items, lambda action: action.trigger(), "Type a command...")

    def _show_quick_open(self):
        open_paths = [e.file_path for e in self._editors() if e.file_path]
        root = self.current_workspace
        items = [(os.path.basename(p), "open  \u2022  " + os.path.relpath(p, root), p) for p in open_paths]
        seen = {os.path.normcase(p) for p in open_paths}
        for rel in list_workspace_files(root, limit=8000):
            absolute = os.path.join(root, rel)
            if os.path.normcase(absolute) not in seen:
                items.append((os.path.basename(rel), os.path.dirname(rel), absolute))
        self._show_popup(items, self._open_path, "Go to file...")

    def _show_symbol_palette(self):
        editor = self.current_editor()
        if editor is None:
            return
        symbols = extract_symbols(editor.text(), editor.language.key)
        items = [(s.name, f"{s.kind}  \u2022  line {s.line + 1}", s.line + 1) for s in symbols]
        self._show_popup(items, self._goto_line_in_current, "Go to symbol...")

    def _trigger_find(self):
        editor = self.current_editor()
        if editor is None:
            return
        self.find_bar.show_find(editor.selectedText() if editor.hasSelectedText() else "")

    def _trigger_replace(self):
        editor = self.current_editor()
        if editor is None:
            return
        self.find_bar.show_replace(editor.selectedText() if editor.hasSelectedText() else "")

    def _find_next(self):
        self.last_search_text = self.find_bar.find_input.text()
        self.find_bar.find_next()

    def _find_previous(self):
        self.find_bar.find_previous()

    def _find_in_files(self):
        editor = self.current_editor()
        self.sidebar.setCurrentWidget(self.search_panel)
        self.sidebar.show()
        self.search_panel.focus_query(editor.selectedText() if editor is not None and editor.hasSelectedText() else "")

    def _trigger_select_all(self):
        self._with_editor(lambda e: e.selectAll())

    def _trigger_goto_line(self):
        editor = self.current_editor()
        if editor is None:
            return
        line, _ = editor.getCursorPosition()
        line_number, accepted = QInputDialog.getInt(self, "Go to Line", "Line number:", line + 1, 1, editor.lines())
        if accepted:
            editor.go_to_line(line_number)

    def _toggle_file_tree(self):
        self.sidebar.setVisible(self.sidebar.isHidden())

    def _show_sidebar(self, index):
        self.sidebar.show()
        self.sidebar.setCurrentIndex(index)

    def _toggle_console_panel(self):
        self.output_panel.setVisible(self.output_panel.isHidden())

    def _show_bottom(self, index):
        self.output_panel.show()
        self.bottom_tabs.setCurrentIndex(index)

    def _toggle_terminal(self):
        if self.output_panel.isVisible() and self.bottom_tabs.currentWidget() is self.terminal_page:
            self.output_panel.hide()
        else:
            self._show_bottom(2)
            self.terminal_page.input.setFocus()

    def _on_bottom_tab_changed(self, index):
        if self.bottom_tabs.widget(index) is self.terminal_page:
            self.terminal_page.ensure_started(self.current_workspace)

    def _change_zoom(self, delta):
        self.editor_zoom = max(-5, min(12, self.editor_zoom + delta))
        for editor in self._editors():
            editor.zoomTo(self.editor_zoom)
        self.settings.setValue("editor_zoom", self.editor_zoom)
        self.statusBar().showMessage(f"Editor zoom: {100 + self.editor_zoom * 10}%", 2000)

    def _zoom_in(self):
        self._change_zoom(1)

    def _zoom_out(self):
        self._change_zoom(-1)

    def _reset_zoom(self):
        self.editor_zoom = 0
        for editor in self._editors():
            editor.zoomTo(0)
        self.settings.setValue("editor_zoom", 0)
        self.statusBar().showMessage("Editor zoom reset to 100%", 2000)

    def _toggle_word_wrap(self, enabled=None):
        editor = self.current_editor()
        if editor is None:
            return
        if enabled is None:
            enabled = editor.wrapMode() == QsciScintilla.WrapMode.WrapNone
        self.prefs["word_wrap"] = bool(enabled)
        for each in self._editors():
            each.apply_options({"word_wrap": bool(enabled)})
        self.word_wrap_action.blockSignals(True)
        self.word_wrap_action.setChecked(bool(enabled))
        self.word_wrap_action.blockSignals(False)

    def _toggle_whitespace(self, enabled):
        self.prefs["show_whitespace"] = bool(enabled)
        for editor in self._editors():
            editor.apply_options({"show_whitespace": bool(enabled)})

    def _trigger_auto_format(self):
        editor = self.current_editor()
        if editor is not None:
            engine = editor.auto_format_code()
            self.statusBar().showMessage(f"Formatted ({engine})", 2500)

    def _apply_output_colors(self):
        palette = get_theme(self.current_theme)
        self.output_page.view.set_colors(palette)
        self.terminal_page.view.set_colors(palette)

    def _set_theme(self, theme_name):
        self.current_theme = theme_name if theme_name in THEMES else "dark"
        self.prefs["theme"] = self.current_theme
        self.setStyleSheet(THEME_STYLESHEETS[self.current_theme])
        self.settings.setValue("theme", self.current_theme)
        for editor in self._editors():
            editor.set_theme(self.current_theme)
        self._apply_output_colors()
        for key, action in self.theme_actions.items():
            action.setChecked(key == self.current_theme)

    def _open_settings(self):
        dialog = SettingsDialog(self.prefs, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new = dialog.values()
        for key, value in new.items():
            self.prefs[key] = coerce(key, value)
        self._save_prefs()
        if self.prefs["theme"] != self.current_theme:
            self._set_theme(self.prefs["theme"])
        options = editor_options(self.prefs)
        for editor in self._editors():
            editor.apply_options(options)
        self.word_wrap_action.blockSignals(True)
        self.word_wrap_action.setChecked(self.prefs["word_wrap"])
        self.word_wrap_action.blockSignals(False)
        self.whitespace_action.blockSignals(True)
        self.whitespace_action.setChecked(self.prefs["show_whitespace"])
        self.whitespace_action.blockSignals(False)
        self._restart_autosave()
        self._schedule_analysis(immediate=True)
        self._update_cursor_status()

    def _preview_kind(self, editor):
        key = editor.language.key
        return "markdown" if key == "markdown" else ("html" if key in ("html", "xml") else None)

    def _open_preview_for_current(self):
        editor = self.current_editor()
        if editor is None:
            return
        kind = self._preview_kind(editor)
        if kind is None:
            self.statusBar().showMessage("Preview is available for HTML and Markdown files", 3000)
            return
        self._preview_html(editor, kind=kind)

    def _preview_html(self, editor, source_title="", kind="html"):
        source_index = self.editor_tabs.indexOf(editor)
        if not source_title and source_index >= 0:
            source_title = self.editor_tabs.tabText(source_index).removesuffix(" *")
        source_title = source_title or "Untitled.html"
        preview_title = f"Preview: {source_title}"
        base_path = editor.file_path or self.current_workspace
        base_dir = os.path.dirname(base_path) if editor.file_path else base_path
        base_dir = os.path.abspath(base_dir or os.getcwd())

        preview = None
        for index in range(self.editor_tabs.count()):
            candidate = self.editor_tabs.widget(index)
            if isinstance(candidate, AnoterraHtmlPreview) and candidate.source_editor is editor:
                preview = candidate
                self.editor_tabs.setTabText(index, preview_title)
                break
        if preview is None:
            preview = AnoterraHtmlPreview(editor, self, kind=kind, base_dir=base_dir)
            self.editor_tabs.addTab(preview, preview_title)
        preview.kind = kind
        preview.base_dir = base_dir
        preview.refresh()
        self.editor_tabs.setCurrentWidget(preview)
        self.statusBar().showMessage("Live preview opened (JavaScript is not supported here).", 5000)

    def _execute_code(self, mode="run"):
        widget = self.editor_tabs.currentWidget()
        if isinstance(widget, AnoterraHtmlPreview):
            widget = widget.source_editor
        if not isinstance(widget, AnoterraEditor):
            return
        current_editor = widget
        tab_index = self.editor_tabs.indexOf(current_editor)
        tab_title = self.editor_tabs.tabText(tab_index).removesuffix(" *") if tab_index >= 0 else ""
        source_name = current_editor.file_path or tab_title
        extension = os.path.splitext(source_name)[1].lower()
        view = self.output_page.view

        if extension in (".html", ".htm", ".md", ".markdown"):
            view.clear()
            self._show_bottom(0)
            kind = "markdown" if extension in (".md", ".markdown") else "html"
            view.append_text(f"[Preview] {source_name} - live preview opened"
                             + (" (JavaScript is not run by the built-in preview)\n" if kind == "html" else "\n"), "info")
            self._preview_html(current_editor, tab_title, kind=kind)
            return

        if not current_editor.file_path:
            self._save_editor(current_editor)
            if not current_editor.file_path:
                return
        elif self.prefs["save_before_run"] and current_editor.is_modified_flag:
            self._save_editor(current_editor)

        self._stop_execution(silent=True)
        view.clear()
        self._show_bottom(0)
        path = current_editor.file_path
        self._run_cwd = os.path.dirname(os.path.abspath(path))
        args = self.run_args.get(path, [])
        label = "RUN" if mode == "run" else "DEBUG"
        view.append_text(f"[{label}] {path}" + (f"  {' '.join(args)}" if args else "") + "\n", "info")

        runner = CodeRunnerEngine(path, run_mode=mode, args=args, timeout=self.prefs["run_timeout"],
                                  python_exe=self.prefs["python_path"] or None, parent=self)
        self.active_runner = runner
        runner.output_signal.connect(lambda text: view.append_text(text, "out"))
        runner.error_signal.connect(lambda text: view.append_text(text, "err"))
        runner.finished_signal.connect(lambda code, metrics, r=runner: self._on_execution_finished(code, metrics, r))
        self.output_page.set_running(True, f"Running {os.path.basename(path)}...")
        runner.start()

    def _run_with_arguments(self):
        editor = self.current_editor()
        if editor is None:
            return
        if not editor.file_path:
            self._save_editor(editor)
            if not editor.file_path:
                return
        current = " ".join(shlex.quote(a) for a in self.run_args.get(editor.file_path, []))
        text, accepted = QInputDialog.getText(self, "Run with Arguments", "Command-line arguments:",
                                              QLineEdit.EchoMode.Normal, current)
        if accepted:
            try:
                self.run_args[editor.file_path] = shlex.split(text, posix=os.name != "nt")
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid arguments", str(exc))
                return
            self._execute_code("run")

    def _send_program_input(self, text):
        if self.active_runner is not None:
            self.active_runner.send_input(text)

    def _stop_execution(self, silent=False):
        if self.active_runner is not None and self.active_runner.is_running:
            self.active_runner.stop()
            if not silent:
                self.statusBar().showMessage("Stopping process...", 2000)

    def _on_execution_finished(self, exit_code, metrics, runner=None):
        if runner is not None and runner is not self.active_runner:
            return
        view = self.output_page.view
        metrics = metrics or {}
        duration = format_duration(metrics["duration"]) if "duration" in metrics else ""
        if metrics.get("timed_out"):
            view.append_text(f"\n[Timed out after {self.prefs['run_timeout']} s]\n", "err")
        elif metrics.get("stopped"):
            view.append_text("\n[Stopped by user]\n", "err")
        else:
            kind = "ok" if exit_code == 0 else "err"
            view.append_text(f"\n[Process exited with code {exit_code}" + (f" in {duration}" if duration else "") + "]\n", kind)
        if "memory_mb" in metrics:
            view.append_text(
                f"[Performance] CPU avg {metrics.get('cpu_percent', 0)}% (peak {metrics.get('peak_cpu_percent', 0)}%) | "
                f"Peak RAM {metrics.get('memory_mb', 0):.2f} MB | Threads {metrics.get('threads', 0)}\n", "info")
        self.output_page.set_running(False, f"Finished (exit code {exit_code})" + (f" in {duration}" if duration else ""))
        self.statusBar().showMessage(f"Execution finished with code {exit_code}", 4000)

    def _restore_session(self):
        files = self.settings.value("session_files", [])
        if isinstance(files, str):
            files = [files] if files else []
        current = str(self.settings.value("session_current", ""))
        for path in files or []:
            if isinstance(path, str) and os.path.isfile(path):
                self._open_path(path)
        if current:
            editor = self._find_open_editor(current)
            if editor is not None:
                self.editor_tabs.setCurrentWidget(editor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self._open_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event):
        dirty = [e for e in self._editors() if e.is_modified_flag]
        if dirty and not self._testing:
            reply = QMessageBox.question(
                self, "Unsaved Changes", f"{len(dirty)} file(s) have unsaved changes.",
                QMessageBox.StandardButton.SaveAll | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.SaveAll:
                for editor in dirty:
                    if not self._save_editor(editor):
                        event.ignore()
                        return
        if self.active_runner is not None:
            self.active_runner.stop()
        self.terminal_page.kill()
        if not self._testing:
            paths = [e.file_path for e in self._editors() if e.file_path]
            current = self.current_editor()
            self.settings.setValue("session_files", paths)
            self.settings.setValue("session_current", current.file_path if current and current.file_path else "")
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("workspace", self.current_workspace)
        self.settings.setValue("main_splitter_sizes", self.main_splitter.sizes())
        self.settings.setValue("output_splitter_sizes", self.output_splitter.sizes())
        self.settings.setValue("editor_zoom", self.editor_zoom)
        self._save_prefs()
        super().closeEvent(event)

    def _open_help_dialog(self):
        AnoterraHelpDialog(self, self.current_theme).exec()

    def _show_about(self):
        QMessageBox.about(
            self, "About Anoterra",
            "<b>Anoterra IDE</b><br>A flexible, lightweight code editor built with PyQt6 and QScintilla.<br><br>"
            "Press Ctrl+Shift+P to explore every command.",
        )
