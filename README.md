<div align="center">

<img src="anoterra.png" width="80" alt="Anoterra Project">

#  Anoterra

[![PyQt6 Version](https://img.shields.io/badge/PyQt6-GUI%20Framework-blue?style=flat-square&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![QScintilla](https://img.shields.io/badge/Editor-QScintilla-green?style=flat-square&logo=code&logoColor=white)](https://www.riverbankcomputing.com/software/qscintilla/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-orange?style=flat-square&logo=linux&logoColor=white)](https://github.com/arraynothere/Anoterra)

</div>

---

## 🔍 Overview

- **Core Highlights**: Universal syntax lexers, smart auto-completion, dual execution modes (Run & Debug with performance metrics), dynamic workspace management, and an IDE-dark minimalist.
- **Supported Platforms**: Windows (`.exe`) and Linux (`Binary`).

---

## 🛠️ Tech Stack & Dependencies

- **GUI Framework**: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (High-performance native widget rendering)
- **Editor Engine**: [QScintilla](https://www.riverbankcomputing.com/software/qscintilla/) (Advanced text editing, folding, and multi-lexer syntax highlighting)
- **Performance Profiling**: `psutil` (Real-time CPU, RAM, and thread monitoring)
- **Bundler**: [PyInstaller](https://pyinstaller.org/) (Standalone binary packaging)

---

## 📂 Project Structure

```text
Anoterra/
├── main.py             # Application entry point and cross-platform icon handler
├── requirements.txt    # Python package dependencies
├── anoterra.ico        # Windows application icon bundle
├── anoterra.png        # Linux application icon
├── build.spec          # PyInstaller packaging configuration
├── core/               # Core business logic and engine modules
│   ├── __init__.py     # Core package initializer
│   ├── editor.py       # Advanced QScintilla wrapper & auto-formatter
│   └── runner.py       # Asynchronous execution & performance profiler
└── ui/                 # User interface components and themes
    ├── __init__.py     # UI package initializer
    ├── main_window.py  # Main IDE window, menus, workspace tree, & terminal
    └── themes.py       # Dark modern professional stylesheet
```

---

## 🚀 Getting Started & Installation

If you want to run, test, or contribute to this repository locally:

### Prerequisites
Make sure you have [Python](https://www.python.org/) (version 3.8 or newer) installed on your system.

### Installation Steps
1. Clone this repository:
   ```bash
   git clone https://github.com/arraynothere/Anoterra.git
   cd Anoterra
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux:
   source venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

### Building Standalone Executable (.exe / Binary)
To compile Anoterra into a standalone application package without requiring a local Python interpreter:
1. Ensure PyInstaller is installed (`pip install pyinstaller`).
2. Run the build command using the provided specification file:
   ```bash
   pyinstaller build.spec
   ```
3. The standalone application bundle will be generated inside the `dist/Anoterra/` directory.

---

## ⌨️ Shortcuts

Anoterra provides a comprehensive set of shortcuts to maximize your coding efficiency:

| Shortcut | Action Description |
| :--- | :--- |
| `Ctrl + N` | Create a new file tab |
| `Ctrl + O` | Open file dialog |
| `Ctrl + S` | Save active file |
| `Ctrl + D` | Auto-formatting |
| `F5` | Run script (Asynchronous execution) |
| `Ctrl + F5` | Run & Debug |
| `Ctrl + F` | Find text in editor |
| `Ctrl + H` | Replace text in editor |
| `Ctrl + Z` | Undo last action |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Redo action |
| `Ctrl + G` | Goto specific line |
| `F1` | Open documentation and help dialog |

---

## 🎨 Theme

- **Editor & Panel Background**: `#1e1e1e` (Dark Slate Charcoal) and `#252526` for sidebars.
- **Active Line Highlight**: `#2a2d2e` with caret color `#aeafad`.
- **Primary Foreground Text**: `#d4d4d4` (Soft Light Gray).
- **Syntax Highlighting Accents**:
  - Keywords: `#569cd6` (Soft Blue)
  - Strings / Literals: `#ce9178` (Warm Terracotta)
  - Comments: `#6a9955` (Muted Forest Green)
  - Numbers / Constants: `#b5cea8` (Pale Sage Green)
  - Functions: `#dcdcaa` (Soft Yellow)
  - Types / Classes: `#4ec9b0` (Teal / Cyan)
- **Status Bar**: `#007acc` (Professional Accent Blue)

---

## 📄 License

© 2026 - Anoterra. Developed and maintained by [@arraydeveloper](https://github.com/arraynothere).
