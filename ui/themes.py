DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QTabWidget::pane {
    border-top: 1px solid #333333;
    background: #1e1e1e;
}
QTabBar::tab {
    background: #2d2d2d;
    color: #969696;
    padding: 8px 16px;
    border-right: 1px solid #1e1e1e;
    border-bottom: 2px solid transparent;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabBar::tab:selected {
    background: #1e1e1e;
    color: #ffffff;
    border-bottom: 2px solid #007acc;
}
QTabBar::tab:hover {
    background: #383838;
    color: #cccccc;
}
QTreeView, QListView {
    background-color: #252526;
    color: #cccccc;
    border: none;
    font-size: 10pt;
}
QTreeView::item:hover, QListView::item:hover {
    background-color: #2a2d2e;
}
QTreeView::item:selected, QListView::item:selected {
    background-color: #37373d;
    color: #ffffff;
}
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: none;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11pt;
}
QSplitter::handle {
    background-color: #333333;
}
QMenuBar {
    background-color: #333333;
    color: #f1f1f1;
    font-size: 10pt;
}
QMenuBar::item:selected {
    background-color: #007acc;
}
QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #333333;
}
QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-weight: bold;
    font-size: 9pt;
}
"""

LIGHT_THEME_STYLESHEET = """
QMainWindow {
    background-color: #f3f3f3;
    color: #333333;
}
QTabWidget::pane {
    border-top: 1px solid #dcdcdc;
    background: #ffffff;
}
QTabBar::tab {
    background: #e1e1e1;
    color: #666666;
    padding: 8px 16px;
    border-right: 1px solid #cccccc;
    border-bottom: 2px solid transparent;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #000000;
    border-bottom: 2px solid #007acc;
}
QTabBar::tab:hover {
    background: #e8e8e8;
    color: #333333;
}
QTreeView, QListView {
    background-color: #f9f9f9;
    color: #333333;
    border: none;
    font-size: 10pt;
}
QTreeView::item:hover, QListView::item:hover {
    background-color: #ececec;
}
QTreeView::item:selected, QListView::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #000000;
    border: none;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11pt;
}
QSplitter::handle {
    background-color: #dcdcdc;
}
QMenuBar {
    background-color: #e1e1e1;
    color: #333333;
    font-size: 10pt;
}
QMenuBar::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QMenu {
    background-color: #f3f3f3;
    color: #333333;
    border: 1px solid #cccccc;
}
QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-weight: bold;
    font-size: 9pt;
}
"""

DARCULA_THEME_STYLESHEET = """
QMainWindow {
    background-color: #2b2b2b;
    color: #a9b7c6;
}
QTabWidget::pane {
    border-top: 1px solid #323232;
    background: #2b2b2b;
}
QTabBar::tab {
    background: #3c3f41;
    color: #909090;
    padding: 8px 16px;
    border-right: 1px solid #2b2b2b;
    border-bottom: 2px solid transparent;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabBar::tab:selected {
    background: #2b2b2b;
    color: #ffc66d;
    border-bottom: 2px solid #4e82b4;
}
QTabBar::tab:hover {
    background: #323232;
    color: #cbccc6;
}
QTreeView, QListView {
    background-color: #313335;
    color: #bbbbbb;
    border: none;
    font-size: 10pt;
}
QTreeView::item:hover, QListView::item:hover {
    background-color: #2f3235;
}
QTreeView::item:selected, QListView::item:selected {
    background-color: #214283;
    color: #ffffff;
}
QTextEdit, QPlainTextEdit {
    background-color: #2b2b2b;
    color: #a9b7c6;
    border: none;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11pt;
}
QSplitter::handle {
    background-color: #323232;
}
QMenuBar {
    background-color: #3c3f41;
    color: #bbbbbb;
    font-size: 10pt;
}
QMenuBar::item:selected {
    background-color: #214283;
    color: #ffffff;
}
QMenu {
    background-color: #3c3f41;
    color: #bbbbbb;
    border: 1px solid #323232;
}
QMenu::item:selected {
    background-color: #214283;
    color: #ffffff;
}
QStatusBar {
    background-color: #3c3f41;
    color: #a9b7c6;
    font-weight: bold;
    font-size: 9pt;
}
"""

THEMES = {
    "Default (Dark)": DARK_THEME_STYLESHEET,
    "Light": LIGHT_THEME_STYLESHEET,
    "Darcula": DARCULA_THEME_STYLESHEET,
}
