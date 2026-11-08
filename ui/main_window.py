import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTreeView, QTextEdit, QFileDialog, QMessageBox,
    QToolBar, QLabel, QMenuBar, QMenu, QDialog, QTextBrowser
)
from PyQt6.QtGui import QAction, QFileSystemModel, QKeySequence
from PyQt6.QtCore import Qt, QModelIndex
from core.editor import AnoterraEditor
from core.runner import CodeRunnerEngine
from ui.themes import DARK_THEME_STYLESHEET

class AnoterraHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anoterra IDE - Documentation & Help")
        self.resize(750, 550)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml("""
            <h2 style='color: #569cd6;'>Anoterra IDE (2026E)</h2>
            <p>Welcome to Anoterra</p>
            
            <h3 style='color: #4ec9b0;'>Keyboard Shortcuts</h3>
            <ul>
                <li><b>Ctrl + N</b>: Create a new file tab</li>
                <li><b>Ctrl + O</b>: Open file</li>
                <li><b>Ctrl + S</b>: Save active file</li>
                <li><b>Ctrl + D</b>: Auto-format code block</li>
                <li><b>F5</b>: Run script (Async Execution)</li>
                <li><b>Ctrl + F5</b>: Run & Debug (Performance Profiling)</li>
                <li><b>Ctrl + F</b>: Find text in editor</li>
                <li><b>Ctrl + H</b>: Find & Replace</li>
                <li><b>Ctrl + Z</b>: Undo</li>
                <li><b>Ctrl + Y / Ctrl + Shift + Z</b>: Redo</li>
            </ul>
            
            <h3 style='color: #4ec9b0;'>Supported Features</h3>
        """)
        browser.setStyleSheet("background-color: #252526; color: #cccccc; border: none; font-family: 'Segoe UI'; font-size: 11pt;")
        layout.addWidget(browser)

class AnoterraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anoterra IDE - 2026E")
        self.resize(1350, 850)
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        
        self.current_workspace = os.path.expanduser("~")
        self.active_runner = None
        
        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.current_workspace)
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(self.current_workspace))
        for i in range(1, 4):
            self.file_tree.setColumnHidden(i, True)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.doubleClicked.connect(self._on_file_double_clicked)
        self.main_splitter.addWidget(self.file_tree)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(right_splitter)

        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_tab)
        right_splitter.addWidget(self.editor_tabs)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        terminal_header = QWidget()
        terminal_header.setStyleSheet("background-color: #2d2d2d; color: #ffffff; padding: 4px;")
        t_layout = QHBoxLayout(terminal_header)
        t_layout.setContentsMargins(8, 2, 8, 2)
        t_layout.addWidget(QLabel("CONSOLE OUTPUT & DEBUGGER LOGS"))
        bottom_layout.addWidget(terminal_header)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #4ec9b0; font-family: 'Consolas'; font-size: 10pt;")
        bottom_layout.addWidget(self.console_output)
        right_splitter.addWidget(bottom_widget)

        self.main_splitter.setSizes([250, 1100])
        right_splitter.setSizes([600, 250])

        self._init_menus_and_toolbars()
        self._create_new_tab("Untitled.py")

    def _init_menus_and_toolbars(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        new_act = QAction("New File", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(lambda: self._create_new_tab("Untitled.py"))
        file_menu.addAction(new_act)

        open_file_act = QAction("Open File...", self)
        open_file_act.setShortcut(QKeySequence.StandardKey.Open)
        open_file_act.triggered.connect(self._open_file_dialog)
        file_menu.addAction(open_file_act)

        open_ws_act = QAction("Open Workspace Folder...", self)
        open_ws_act.triggered.connect(self._open_workspace_folder)
        file_menu.addAction(open_ws_act)

        file_menu.addSeparator()
        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self._save_active_file)
        file_menu.addAction(save_act)

        edit_menu = menubar.addMenu("&Edit")
        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(self._trigger_undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        redo_act.triggered.connect(self._trigger_redo)
        edit_menu.addAction(redo_act)
        edit_menu.addSeparator()

        find_act = QAction("Find...", self)
        find_act.setShortcut(QKeySequence.StandardKey.Find)
        find_act.triggered.connect(self._trigger_find)
        edit_menu.addAction(find_act)

        replace_act = QAction("Replace...", self)
        replace_act.setShortcut(QKeySequence.StandardKey.Replace)
        replace_act.triggered.connect(self._trigger_replace)
        edit_menu.addAction(replace_act)

        selection_menu = menubar.addMenu("&Selection")
        sel_all_act = QAction("Select All", self)
        sel_all_act.setShortcut(QKeySequence.StandardKey.SelectAll)
        sel_all_act.triggered.connect(self._trigger_select_all)
        selection_menu.addAction(sel_all_act)

        view_menu = menubar.addMenu("&View")
        toggle_side_act = QAction("Toggle File Explorer", self)
        toggle_side_act.triggered.connect(self._toggle_file_tree)
        view_menu.addAction(toggle_side_act)

        goto_menu = menubar.addMenu("&Goto")
        goto_line_act = QAction("Goto Line...", self)
        goto_line_act.setShortcut(QKeySequence("Ctrl+G"))
        goto_line_act.triggered.connect(self._trigger_goto_line)
        goto_menu.addAction(goto_line_act)

        run_menu = menubar.addMenu("&Execution")
        run_act = QAction("Run Script", self)
        run_act.setShortcut(QKeySequence("F5"))
        run_act.triggered.connect(lambda: self._execute_code("run"))
        run_menu.addAction(run_act)

        debug_act = QAction("Run & Debug", self)
        debug_act.setShortcut(QKeySequence("Ctrl+F5"))
        debug_act.triggered.connect(lambda: self._execute_code("debug"))
        run_menu.addAction(debug_act)

        help_menu = menubar.addMenu("&Help")
        docs_act = QAction("Documentation & Shortcuts", self)
        docs_act.setShortcut(QKeySequence("F1"))
        docs_act.triggered.connect(self._open_help_dialog)
        help_menu.addAction(docs_act)

        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        btn_run = QAction("Run", self)
        btn_run.triggered.connect(lambda: self._execute_code("run"))
        self.toolbar.addAction(btn_run)

        btn_debug = QAction("Run & Debug", self)
        btn_debug.triggered.connect(lambda: self._execute_code("debug"))
        self.toolbar.addAction(btn_debug)

        self.toolbar.addSeparator()
        btn_format = QAction("Auto-Format (Ctrl+D)", self)
        btn_format.triggered.connect(self._trigger_auto_format)
        self.toolbar.addAction(btn_format)

        self.statusBar().showMessage("Anoterra IDE v2026.0E")

    def _create_new_tab(self, title, file_path=None, content=""):
        editor = AnoterraEditor(file_path=file_path)
        if content:
            editor.setText(content)
        idx = self.editor_tabs.addTab(editor, title)
        self.editor_tabs.setCurrentIndex(idx)

    def _on_file_double_clicked(self, index: QModelIndex):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._create_new_tab(os.path.basename(file_path), file_path=file_path, content=content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\n{str(e)}")

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", self.current_workspace)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._create_new_tab(os.path.basename(file_path), file_path=file_path, content=content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")

    def _open_workspace_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Workspace Folder", self.current_workspace)
        if folder_path:
            self.current_workspace = folder_path
            self.file_model.setRootPath(folder_path)
            self.file_tree.setRootIndex(self.file_model.index(folder_path))
            self.statusBar().showMessage(f"Workspace loaded: {folder_path}", 4000)

    def _save_active_file(self):
        current_editor = self.editor_tabs.currentWidget()
        if not isinstance(current_editor, AnoterraEditor):
            return

        if not current_editor.file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", self.current_workspace)
            if not file_path:
                return
            current_editor.file_path = file_path
            self.editor_tabs.setTabText(self.editor_tabs.currentIndex(), os.path.basename(file_path))

        try:
            with open(current_editor.file_path, "w", encoding="utf-8") as f:
                f.write(current_editor.text())
            current_editor.is_modified_flag = False
            self.statusBar().showMessage(f"Saved: {current_editor.file_path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")

    def _close_tab(self, index):
        editor = self.editor_tabs.widget(index)
        if isinstance(editor, AnoterraEditor) and editor.is_modified_flag:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save changes before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_active_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        self.editor_tabs.removeTab(index)

    def _trigger_undo(self):
        editor = self.editor_tabs.currentWidget()
        if isinstance(editor, AnoterraEditor):
            editor.undo()

    def _trigger_redo(self):
        editor = self.editor_tabs.currentWidget()
        if isinstance(editor, AnoterraEditor):
            editor.redo()

    def _trigger_find(self):
        editor = self.editor_tabs.currentWidget()
        if isinstance(editor, AnoterraEditor):
            editor.findFirst("", False, False, False, True)

    def _trigger_replace(self):
        pass

    def _trigger_select_all(self):
        editor = self.editor_tabs.currentWidget()
        if isinstance(editor, AnoterraEditor):
            editor.selectAll()

    def _toggle_file_tree(self):
        if self.file_tree.isVisible():
            self.file_tree.hide()
        else:
            self.file_tree.show()

    def _trigger_goto_line(self):
        pass

    def _trigger_auto_format(self):
        current_editor = self.editor_tabs.currentWidget()
        if isinstance(current_editor, AnoterraEditor):
            current_editor.auto_format_code()
            self.statusBar().showMessage("Auto-formatted successfully", 2000)

    def _open_help_dialog(self):
        dialog = AnoterraHelpDialog(self)
        dialog.exec()

    def _execute_code(self, mode="run"):
        current_editor = self.editor_tabs.currentWidget()
        if not isinstance(current_editor, AnoterraEditor):
            return

        if not current_editor.file_path:
            self._save_active_file()
            if not current_editor.file_path:
                return

        self.console_output.clear()
        self.console_output.append(f"[{'RUN' if mode=='run' else 'DEBUG'}] Starting execution for: {current_editor.file_path}\n")

        self.active_runner = CodeRunnerEngine(current_editor.file_path, run_mode=mode)
        self.active_runner.output_signal.connect(self.console_output.insertPlainText)
        self.active_runner.finished_signal.connect(self._on_execution_finished)
        self.active_runner.start()

    def _on_execution_finished(self, exit_code, metrics):
        if metrics:
            self.console_output.append(f"\n[Performance Metrics] CPU: {metrics.get('cpu_percent', 0)}% | RAM: {metrics.get('memory_mb', 0):.2f} MB | Threads: {metrics.get('threads', 0)}")
        self.statusBar().showMessage(f"Execution finished with code {exit_code}", 4000)
