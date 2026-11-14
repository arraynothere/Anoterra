"""Qt stylesheets generated from the palettes in ``core.theme_data``."""
from string import Template

from core.theme_data import THEMES, get_theme

_QSS = Template(r"""
QMainWindow, QWidget { background: $bg; color: $fg; font-family: 'Segoe UI', 'Inter', 'Noto Sans', sans-serif; font-size: 10pt; }
QDialog { background: $bg; }
QMenuBar, QToolBar { background: $panel; color: $fg; border: 0; spacing: 6px; padding: 5px; }
QMenuBar::item, QToolButton { padding: 6px 10px; border-radius: 5px; background: transparent; }
QMenuBar::item:selected, QToolButton:hover { background: $hover; }
QToolButton:checked { background: $accent_soft; border: 1px solid $accent; }
QToolTip { background: $elevated; color: $fg; border: 1px solid $border; padding: 4px 6px; }
QTabWidget::pane { border: 1px solid $border; border-radius: 6px; background: $bg; top: -1px; }
QTabBar { background: transparent; }
QTabBar::tab { background: $panel; color: $muted; padding: 8px 14px; border: 1px solid $border; border-bottom: 0; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 3px; }
QTabBar::tab:selected { background: $bg; color: $fg; border-top: 2px solid $accent; }
QTabBar::tab:hover { color: $fg; background: $hover; }
QTreeView, QListView, QTableView { background: $tree; alternate-background-color: $panel; color: $fg; border: 0; outline: 0; padding: 5px; }
QTreeView::item, QListView::item { padding: 4px 3px; border-radius: 4px; }
QTreeView::item:hover, QListView::item:hover { background: $hover; }
QTreeView::item:selected, QListView::item:selected { background: $accent_soft; color: $fg; }
QHeaderView::section { background: $panel; color: $muted; border: 0; padding: 4px 8px; }
QTextEdit, QPlainTextEdit, QTextBrowser, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox { background: $input_bg; color: $fg; border: 1px solid $border; border-radius: 5px; selection-background-color: $selection; selection-color: $fg; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { padding: 6px 8px; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus { border: 1px solid $accent; }
QComboBox QAbstractItemView { background: $elevated; color: $fg; border: 1px solid $border; selection-background-color: $accent_soft; selection-color: $fg; }
QComboBox::drop-down { border: 0; width: 22px; }
QCheckBox, QRadioButton, QLabel, QGroupBox { background: transparent; }
QCheckBox { spacing: 8px; }
QGroupBox { border: 1px solid $border; border-radius: 6px; margin-top: 10px; padding: 12px 8px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: $muted; }
QPushButton { background: $btn; color: #ffffff; border: 0; border-radius: 5px; padding: 7px 14px; }
QPushButton:hover { background: $btn_hover; }
QPushButton:pressed { background: $btn_pressed; }
QPushButton:disabled { background: $border; color: $muted; }
QPushButton[flat="true"], QToolButton[flat="true"] { background: transparent; color: $fg; border: 1px solid transparent; padding: 3px 8px; }
QPushButton[flat="true"]:hover { background: $hover; }
QPushButton[secondary="true"] { background: $panel; color: $fg; border: 1px solid $border; }
QPushButton[secondary="true"]:hover { background: $hover; }
QSplitter::handle { background: $border; }
QSplitter::handle:hover { background: $accent; }
QMenu { background: $elevated; color: $fg; border: 1px solid $border; padding: 4px; }
QMenu::item { padding: 7px 28px 7px 10px; border-radius: 4px; }
QMenu::item:selected { background: $accent_soft; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }
QStatusBar { background: $panel; color: $muted; border-top: 1px solid $border; }
QStatusBar::item { border: 0; }
QStatusBar QToolButton { padding: 2px 8px; border-radius: 3px; color: $muted; }
QStatusBar QToolButton:hover { background: $hover; color: $fg; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: $scroll; min-height: 24px; border-radius: 5px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: $scroll; min-width: 24px; border-radius: 5px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
#FindBar { background: $panel; border-bottom: 1px solid $border; }
#FindBar QLineEdit[invalid="true"] { border: 1px solid $error; }
#PaletteFrame { background: $elevated; border: 1px solid $border; border-radius: 10px; }
#PaletteFrame QLineEdit { border: 0; border-bottom: 1px solid $border; border-radius: 0; font-size: 11pt; padding: 10px 12px; background: $elevated; }
#PaletteFrame QListWidget { background: $elevated; }
#WelcomePage, #WelcomePage QWidget { background: $bg; }
#WelcomeTitle { font-size: 26pt; font-weight: 600; color: $fg; }
#WelcomeSub { color: $muted; font-size: 11pt; }
#PanelHeader { background: $panel; color: $muted; padding: 4px 8px; font-weight: 600; }
#Breadcrumbs { padding: 4px 8px; font-size: 11px; background: $panel; color: $fg; border-bottom: 1px solid $border; }
#OutputView { font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace; font-size: 10pt; }
""")

def build_stylesheet(name):
    palette = get_theme(name)
    return _QSS.substitute(palette)

THEME_STYLESHEETS = {name: build_stylesheet(name) for name in THEMES}
DARK_THEME_STYLESHEET = THEME_STYLESHEETS["dark"]
LIGHT_THEME_STYLESHEET = THEME_STYLESHEETS["light"]

__all__ = [
    "THEME_STYLESHEETS", "THEMES", "DARK_THEME_STYLESHEET",
    "LIGHT_THEME_STYLESHEET", "build_stylesheet", "get_theme",
]
