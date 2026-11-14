<div align="center">

<img src="anoterra.png" width="80" alt="Anoterra Project">

#  Anoterra

[![PyQt6 Version](https://img.shields.io/badge/PyQt6-GUI%20Framework-blue?style=flat-square&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![QScintilla](https://img.shields.io/badge/Editor-QScintilla-green?style=flat-square&logo=code&logoColor=white)](https://www.riverbankcomputing.com/software/qscintilla/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=flat-square&logo=linux&logoColor=white)](https://github.com/arraynothere/Anoterra)

</div>

---

## <img src="https://img.shields.io/badge/Section-Overview-007acc?style=flat-square&logo=readme&logoColor=white" alt="Overview"> Overview

- **Core Highlights**: Universal syntax lexers, smart auto-completion, dual execution modes (Run & Debug with performance metrics), a Python step debugger with breakpoints, dynamic workspace management, and an IDE-dark minimalist.
- **Supported Platforms**: Windows (`.exe`) and Linux (`Binary`) officially; macOS via source (see [Supported Devices](#-supported-devices)).

---

## <img src="https://img.shields.io/badge/Section-Tech_Stack-6f42c1?style=flat-square&logo=codeforces&logoColor=white" alt="Tech Stack"> Tech Stack & Dependencies

- **GUI Framework**: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (High-performance native widget rendering)
- **Editor Engine**: [QScintilla](https://www.riverbankcomputing.com/software/qscintilla/) (Advanced text editing, folding, and multi-lexer syntax highlighting)
- **Performance Profiling**: `psutil` (Real-time CPU, RAM, and thread monitoring)
- **Python Formatting**: [Black](https://black.readthedocs.io/) (auto-format with `Ctrl + D`)
- **Debugger**: standard-library `bdb` running in a separate process (no extra dependency)
- **Bundler**: [PyInstaller](https://pyinstaller.org/) (Standalone binary packaging, build-only: `requirements-build.txt`)

---

## <img src="https://img.shields.io/badge/Section-Project_Structure-28a745?style=flat-square&logo=git&logoColor=white" alt="Structure"> Project Structure

```text
Anoterra/
├── main.py             # Application entry point and cross-platform icon handler
├── requirements.txt    # Runtime dependencies
├── requirements-build.txt # Runtime + PyInstaller (build only)
├── LICENSE             # MIT License
├── anoterra.ico        # Windows application icon bundle
├── anoterra.png        # Linux application icon
├── build.spec          # PyInstaller packaging configuration
├── core/               # Core business logic and engine modules
│   ├── __init__.py     # Core package initializer
│   ├── analysis.py     # Code analysis utilities & Black/built-in formatter
│   ├── debug_worker.py # Debug process: runs the script under bdb (stdlib only)
│   ├── debugger.py     # Debug session (socket protocol, Qt signals)
│   ├── editor.py       # Advanced QScintilla wrapper & auto-formatter
│   ├── languages.py    # Language lexers and configurations
│   ├── runner.py       # Asynchronous execution & performance profiler
│   ├── settings.py     # Application configurations and preferences
│   ├── theme_data.py   # Theme color palettes and configuration
│   ├── trust.py        # Workspace Trust helpers (plugins)
│   └── utils.py        # Helper utilities and common functions
├── tests/              # Test suite and smoke testing
│   ├── __init__.py     # Test environment setup (offscreen Qt)
│   ├── test_hardening.py           # Plugin opt-in & path helper tests
│   ├── test_debug_worker.py        # Debugger protocol tests (breakpoints, stepping)
│   ├── test_debugger_ui.py         # Breakpoint markers & Debug tab tests
│   ├── test_trust.py               # Workspace Trust tests
│   ├── test_black_format.py        # Black formatting tests
│   ├── test_app_smoke.py           # Application smoke tests
│   ├── test_core_logic.py          # Core logic verification tests
│   ├── test_editor_view_options.py # Editor view options unit tests
│   ├── test_features.py            # Feature integration tests
│   ├── test_html_preview.py        # HTML preview functional tests
│   ├── test_ide_upgrades.py        # IDE enhancement tests
│   └── test_theme.py               # Theme rendering unit tests
└── ui/                 # User interface components and themes
    ├── __init__.py     # UI package initializer
    ├── debug_panel.py  # Debug tab (variables, call stack) & debug controller
    ├── main_window.py  # Main IDE window, menus, workspace tree, & terminal
    ├── themes.py       # Dark modern professional stylesheet
    └── widgets.py      # Custom user interface widgets
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

Anoterra is a **desktop-only** app (PyQt6). It does **not** run on phones/tablets or in a browser.

| OS / Device | Architecture | Status | How to run |
| :--- | :--- | :---: | :--- |
| **Windows 10 / 11** | x64 | ✅ Official | `.exe` build or from source |
| **Linux** (Ubuntu 20.04+, Debian 11+, Fedora, Arch, glibc ≥ 2.28) | x86_64 | ✅ Official | Binary build or from source |
| **Linux on ARM** (Raspberry Pi 4/5 64-bit, ARM laptops) | aarch64 | ⚠️ From source only | `pip install -r requirements.txt` (needs PyQt6 wheels for your distro) |
| **macOS 11+** (Intel & Apple Silicon) | x64 / arm64 | ⚠️ From source, not officially tested | `python main.py` |
| **Windows 7 / 8 / 8.1, 32-bit Windows** | - | ❌ Not supported | PyQt6 requires Windows 10+ 64-bit |
| **Android / iOS / iPadOS** | - | ❌ Not supported | Desktop toolkit only |
| **ChromeOS / Web browser** | - | ❌ Not supported | Only via a Linux container (Crostini) from source |

**Requirements**
* **Python**: 3.9 or newer (when running from source).
* **RAM**: 512 MB minimum, 1 GB+ recommended. **Storage**: ~100 MB. **CPU**: dual-core, no dedicated GPU needed.
* **Linux**: Qt 6.5+ needs `libxcb-cursor0` (`sudo apt install libxcb-cursor0`). Both X11 and Wayland (XWayland) work.
* **To run code**: the matching compiler/interpreter (Python, Node.js, g++, Rust, Go, JDK, etc.) must be installed and available in `PATH`.

---

## <img src="https://img.shields.io/badge/Section-Getting_Started-e83e8c?style=flat-square&logo=python&logoColor=white" alt="Getting Started"> Getting Started & Installation

If you want to run, test, or contribute to this repository locally:

### Prerequisites
Make sure you have [Python](https://www.python.org/) (version 3.9 or newer) installed on your system.

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
5. Run the tests (optional):
   ```bash
   python -m unittest discover -s tests -t .
   ```

### Building Standalone Executable (.exe / Binary)
To compile Anoterra into a standalone application package without requiring a local Python interpreter:
1. Install build dependencies (`pip install -r requirements-build.txt`).
2. Run the build command using the provided specification file:
   ```bash
   pyinstaller build.spec
   ```
3. A single-file executable is generated at `dist/Anoterra` (`dist/Anoterra.exe` on Windows).

---

## <img src="https://img.shields.io/badge/Section-Pros_%26_Cons-dc3545?style=flat-square&logo=scale&logoColor=white" alt="Pros and Cons"> Pros & Cons

| Feature | Status |
| :--- | :---: |
| Lightweight, starts fast, low RAM usage | ✅ |
| Syntax highlighting for 30+ languages | ✅ |
| Run code for 15 languages (Python, JS/TS, C/C++, Rust, Go, Java, PHP, Ruby, Lua, Perl, Shell, Batch, PowerShell) | ✅ |
| Asynchronous runner with Stop button, timeout & interactive input | ✅ |
| Profiler (CPU, memory, threads) | ✅ |
| Command palette, Quick Open, find/replace (regex), search in files | ✅ |
| Live syntax check (Python/JSON), outline, bookmarks, minimap | ✅ |
| Embedded terminal, HTML & Markdown live preview | ✅ |
| 8 built-in color themes, session restore, autosave | ✅ |
| Plugin system (opt-in, off by default) with Workspace Trust | ✅ |
| Python step debugger: breakpoints, step over/into/out, variables & call stack | ✅ |
| Auto-format Python with Black (included in `requirements.txt`) | ✅ |
| Windows & Linux standalone builds | ✅ |
| Test suite included | ✅ |
| Free & open source (MIT) | ✅ |
| Language Server (LSP) / IntelliSense | ❌ |
| Debugger extras: watch expressions, conditional breakpoints, debugging other threads | ❌ |
| Git integration | ❌ |
| Mobile / Web / 32-bit support | ❌ |
| Official macOS binary | ❌ |
| Compile step of compiled languages can't be cancelled with Stop | ❌ |
| Plugins are not sandboxed: once trusted they run with your full privileges | ❌ |

---

## <img src="https://img.shields.io/badge/Section-Plugins-20c997?style=flat-square&logo=python&logoColor=white" alt="Plugins"> Plugins

Plugins are **disabled by default** because they execute arbitrary Python code. Anoterra uses **Workspace Trust**: a plugin only loads when (1) plugins are enabled **and** (2) the workspace folder is trusted by you.

1. Open **Settings** (`Ctrl + ,`) → **Plugins** tab → tick **Enable plugins**.
2. Create a `plugins/` folder inside your workspace (Anoterra never creates it for you).
3. Add a `.py` file (files starting with `_` are ignored) exposing `register_plugin(window)`:
   ```python
   # <workspace>/plugins/hello.py
   def register_plugin(window):
       window.statusBar().showMessage("Hello from plugin!", 3000)
   ```
4. When plugins are found in a folder you have not trusted yet, Anoterra asks **"Trust this workspace?"**. Choose *Trust Folder and Load Plugins* to load them, or *Don't Trust* to keep the folder in restricted mode (nothing is executed).

**Workspace Trust details**
- Manage it any time with **File → Workspace Trust...** (trust / remove trust for the current folder).
- Trust applies to that exact folder only; subfolders do not inherit it.
- Your home folder and drive roots cannot be trusted as a whole.
- Plugins load right after you trust the folder or enable them in Settings, and on every startup afterwards. Disabling or removing trust takes effect after a restart.
- **Not a sandbox**: after you trust a folder, its plugins can do anything you can do. Trust only sources you know.

---

## <img src="https://img.shields.io/badge/Section-Debugger-e74c3c?style=flat-square&logo=python&logoColor=white" alt="Debugger"> Debugger (Python)

`Ctrl + F5` is still **performance profiling**. The step debugger is a separate command: **Execution -> Start Debugging (Breakpoints)**.

1. Put the cursor on a line and press `F9` (or `Shift + Click` the gutter next to the line number) to set / remove a breakpoint (red dot). A normal click on the gutter still toggles a bookmark.
2. Press `Ctrl + Shift + F5`. The script runs in a separate process until it hits a breakpoint. With no breakpoints it stops on the first line.
3. When paused, the current line is highlighted and the **Debug** tab (bottom panel) shows the **variables** of the selected frame and the **call stack** (click a frame to jump to it).
4. Continue with `F8`, step over `F10`, step into `F11`, step out `Shift + F11`, stop with `Shift + F5`.

Notes: Python files only (`.py`); program input/output works in the **Output** tab as usual; breakpoints you add or remove while the program is paused are applied when you resume; only the main thread is traced.

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
| `Ctrl + F5` | Run & Debug (performance profiling) |
| `Ctrl + Shift + F5` | Start debugging (breakpoints) |
| `F9` | Toggle breakpoint |
| `F8` / `F10` / `F11` / `Shift + F11` | Continue / Step over / Step into / Step out |
| `Ctrl + F` | Find text in editor |
| `Ctrl + H` | Replace text in editor |
| `Ctrl + Z` | Undo last action |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Redo action |
| `Ctrl + G` | Goto specific line |
| `F1` | Open documentation and help dialog |

---

## <img src="https://img.shields.io/badge/Section-Theme-6610f2?style=flat-square&logo=vim&logoColor=white" alt="Theme"> Theme

- **8 built-in themes** (switch in Settings): Anoterra Dark (default), Anoterra Light, Midnight Blue, Mocha Warm, Paper Warm Light, GitHub, Eclipse, Native macOS.
- **Default (Anoterra Dark) palette**:
  - Editor / Window Background: `#17191f`, Panels: `#20232b`, Active Line: `#252a35`
  - Foreground Text: `#e6e9ef`, Accent: `#55b7c9`
  - Keywords `#66aaff` · Strings `#e8a27a` · Comments `#7dbb8c` · Numbers `#d6c28c` · Functions `#e2d28e` · Types `#59c7b2`
- All colors live in `core/theme_data.py`; adding a theme only needs one more dictionary entry.

---

## <img src="https://img.shields.io/badge/Section-Contributors-blueviolet?style=flat-square&logo=github&logoColor=white" alt="Contributors"> Contributors & Project Team

| Role | Name | Badge |
| :--- | :--- | :--- |
| **Developer** | `Array` | [![arraynothere](https://img.shields.io/badge/Owner-@arraynothere-blue?style=for-the-badge&logo=github)](https://github.com/arraynothere) |
| **Contributor** | `Yokoto` | [![Yokoto](https://img.shields.io/badge/Contributor-FynixorStudio-purple?style=for-the-badge&logo=github)](https://github.com/FynixorStudio) |

---

<div align="center">

<br>

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553cc.gif" width="100%" alt="Animated Purple Banner">

<br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=8a2be2&height=120&section=footer&text=%20%20&%20Stay%20Awesome!&fontSize=22&fontColor=ffffff&animation=fadeIn" width="100%" alt="Purple Wave Footer">

<br>

**© 2026 - Anoterra IDE. Developed by [@arraydeveloper](https://github.com/arraynothere).**

</div>
