<div align="center">

<img src="anoterra.png" width="80" alt="Anoterra Project">

#  Anoterra

[![PyQt6 Version](https://img.shields.io/badge/PyQt6-GUI%20Framework-blue?style=flat-square&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![QScintilla](https://img.shields.io/badge/Editor-QScintilla-green?style=flat-square&logo=code&logoColor=white)](https://www.riverbankcomputing.com/software/qscintilla/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-orange?style=flat-square&logo=linux&logoColor=white)](https://github.com/arraynothere/Anoterra)

</div>

---

## <img src="https://img.shields.io/badge/Section-Overview-007acc?style=flat-square&logo=readme&logoColor=white" alt="Overview"> Overview

- **Core Highlights**: Universal syntax lexers, smart auto-completion, dual execution modes (Run & Debug with performance metrics), dynamic workspace management, and an IDE-dark minimalist.
- **Supported Platforms**: Windows (`.exe`) and Linux (`Binary`).

---

## <img src="https://img.shields.io/badge/Section-Tech_Stack-6f42c1?style=flat-square&logo=codeforces&logoColor=white" alt="Tech Stack"> Tech Stack & Dependencies

- **GUI Framework**: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (High-performance native widget rendering)
- **Editor Engine**: [QScintilla](https://www.riverbankcomputing.com/software/qscintilla/) (Advanced text editing, folding, and multi-lexer syntax highlighting)
- **Performance Profiling**: `psutil` (Real-time CPU, RAM, and thread monitoring)
- **Bundler**: [PyInstaller](https://pyinstaller.org/) (Standalone binary packaging)

---

## <img src="https://img.shields.io/badge/Section-Project_Structure-28a745?style=flat-square&logo=git&logoColor=white" alt="Structure"> Project Structure

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

## <img src="https://img.shields.io/badge/Section-How_It_Works-17a2b8?style=flat-square&logo=cisco&logoColor=white" alt="How It Works"> How It Works

**Anoterra** is a lightweight modern desktop-based Code Editor & IDE built using **Python** and **PyQt6/QScintilla**. 

### How Does It Work?
1. **Core Editing Engine**: Utilizes the high-performance *QScintilla* library providing real-time syntax highlighting, code folding, smart auto-completion, and responsive line numbering.
2. **Asynchronous Execution & Runner**: When executing code (`F5` or `Ctrl + F5`), scripts run without blocking the main user interface. The asynchronous engine in `core/runner.py` executes external processes (Python, Node.js, C++ compiler) in the background while monitoring system resource usage (*CPU & RAM* via `psutil`).
3. **Dynamic Workspace**: Provides left-panel project folder workspace management, multi-document file tab navigation, real-time HTML Live Preview, and an integrated terminal.

---

## <img src="https://img.shields.io/badge/Section-Supported_Devices-ffc107?style=flat-square&logo=windows&logoColor=white" alt="Supported Devices"> Supported Devices

Anoterra is designed to be lightweight and optimized across various operating systems:
* **Operating Systems**: 
  * **Windows** (Windows 10 / 11 - 64-bit architecture)
  * **Linux** (Major distributions such as Ubuntu, Debian, Fedora, Arch Linux)
* **Hardware Requirements**:
  * **RAM**: Minimum 512 MB (Extremely lightweight and memory-efficient).
  * **Storage**: Approximately 50 MB - 100 MB free space.
  * **Processor**: Standard dual-core processor (no dedicated GPU required).

---

## <img src="https://img.shields.io/badge/Section-Getting_Started-e83e8c?style=flat-square&logo=python&logoColor=white" alt="Getting Started"> Getting Started & Installation

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

## <img src="https://img.shields.io/badge/Section-Shortcuts-fd7e14?style=flat-square&logo=keyboard&logoColor=white" alt="Shortcuts"> Shortcuts

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

## <img src="https://img.shields.io/badge/Section-Theme-6610f2?style=flat-square&logo=vim&logoColor=white" alt="Theme"> Theme

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
- **Status Bar**: `#007acc` (Professional Accent Blue).

---

<div align="center">

<br>

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553cc.gif" width="100%" alt="Animated Purple Banner">

<br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=8a2be2&height=120&section=footer&text=Keep%20Coding%20&%20Stay%20Awesome!&fontSize=22&fontColor=ffffff&animation=fadeIn" width="100%" alt="Purple Wave Footer">

<br>

**© 2026 - Anoterra IDE. Developed by [@arraydeveloper](https://github.com/arraynothere).**

</div>
