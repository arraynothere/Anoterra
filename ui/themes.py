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
