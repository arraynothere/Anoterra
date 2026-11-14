"""Color palettes shared by the editor (QScintilla) and the Qt stylesheet.

Every theme is one flat dictionary. UI keys style the application chrome,
``ed_*`` / syntax keys style the code editor. Adding a new theme only means
adding one more entry to ``THEMES``.
"""

THEMES = {
    "dark": {
        "label": "Anoterra Dark", "dark": True,
        "bg": "#17191f", "panel": "#20232b", "tree": "#1d2027", "elevated": "#222630",
        "border": "#303541", "fg": "#e6e9ef", "muted": "#aab1c0", "accent": "#55b7c9",
        "accent_soft": "#294158", "btn": "#2f8798", "btn_hover": "#369caf", "btn_pressed": "#246d7b",
        "hover": "#2b303b", "scroll": "#454c5a", "input_bg": "#17191f", "selection": "#345b86",
        "ed_bg": "#17191f", "ed_fg": "#e6e9ef", "margin_bg": "#20232b", "margin_fg": "#9299a8",
        "caret": "#f3f6ff", "caret_line": "#252a35", "sel_bg": "#345b86", "sel_fg": "#ffffff",
        "fold_bg": "#20232b", "guide": "#2f3542", "edge": "#2a2f3a",
        "brace_bg": "#3e3e42", "brace_fg": "#4ec9b0", "bad_brace_bg": "#5a1d1d", "bad_brace_fg": "#f44747",
        "find_hl": "#7a6a2c", "word_hl": "#3a4358", "error": "#f2555a", "warn": "#e5c07b", "bookmark": "#55b7c9",
        "comment": "#7dbb8c", "keyword": "#66aaff", "string": "#e8a27a", "number": "#d6c28c",
        "type": "#59c7b2", "function": "#e2d28e", "operator": "#c9d1e0", "decorator": "#c5a0df",
        "tag": "#66aaff", "attribute": "#91c9e8", "preprocessor": "#c5a0df", "regex": "#e8a27a",
    },
    "light": {
        "label": "Anoterra Light", "dark": False,
        "bg": "#f7f8fb", "panel": "#eef1f6", "tree": "#ffffff", "elevated": "#ffffff",
        "border": "#d7dde7", "fg": "#202532", "muted": "#687184", "accent": "#167d91",
        "accent_soft": "#d5e7f5", "btn": "#167d91", "btn_hover": "#1d92a8", "btn_pressed": "#116979",
        "hover": "#e4eaf3", "scroll": "#b5becd", "input_bg": "#ffffff", "selection": "#c8ddf5",
        "ed_bg": "#ffffff", "ed_fg": "#202532", "margin_bg": "#f0f2f6", "margin_fg": "#6d7482",
        "caret": "#202532", "caret_line": "#f3f6fa", "sel_bg": "#c8ddf5", "sel_fg": "#15243a",
        "fold_bg": "#e7ebf1", "guide": "#e1e6ee", "edge": "#e8ecf2",
        "brace_bg": "#d6e4f2", "brace_fg": "#087d77", "bad_brace_bg": "#f7d4d4", "bad_brace_fg": "#b42318",
        "find_hl": "#f6e08a", "word_hl": "#dbe7f5", "error": "#c62828", "warn": "#9a6700", "bookmark": "#167d91",
        "comment": "#34734b", "keyword": "#145db4", "string": "#a24116", "number": "#8b6500",
        "type": "#087d77", "function": "#7950a1", "operator": "#40485a", "decorator": "#9a347f",
        "tag": "#145db4", "attribute": "#236f9b", "preprocessor": "#9a347f", "regex": "#a24116",
    },
    "midnight": {
        "label": "Midnight Blue", "dark": True,
        "bg": "#0f1220", "panel": "#151a2e", "tree": "#121629", "elevated": "#1b2140",
        "border": "#2a3158", "fg": "#dfe4ff", "muted": "#8f98c9", "accent": "#7c8cff",
        "accent_soft": "#26306a", "btn": "#5b6bdf", "btn_hover": "#7080f0", "btn_pressed": "#4757c4",
        "hover": "#1f2646", "scroll": "#3a4373", "input_bg": "#0f1220", "selection": "#2f3d86",
        "ed_bg": "#0f1220", "ed_fg": "#dfe4ff", "margin_bg": "#151a2e", "margin_fg": "#6b74a8",
        "caret": "#ffffff", "caret_line": "#171d36", "sel_bg": "#2f3d86", "sel_fg": "#ffffff",
        "fold_bg": "#151a2e", "guide": "#222a4d", "edge": "#1c2342",
        "brace_bg": "#2f3a70", "brace_fg": "#7fdbca", "bad_brace_bg": "#5a1d33", "bad_brace_fg": "#ff6b81",
        "find_hl": "#6b5f1f", "word_hl": "#27305c", "error": "#ff6b81", "warn": "#ffcb6b", "bookmark": "#7c8cff",
        "comment": "#5f6caa", "keyword": "#82aaff", "string": "#c3e88d", "number": "#f78c6c",
        "type": "#ffcb6b", "function": "#89ddff", "operator": "#9fb0f0", "decorator": "#c792ea",
        "tag": "#f07178", "attribute": "#ffcb6b", "preprocessor": "#c792ea", "regex": "#89ddff",
    },
    "mocha": {
        "label": "Mocha Warm", "dark": True,
        "bg": "#1e1a17", "panel": "#26211d", "tree": "#221e1a", "elevated": "#2d2722",
        "border": "#3b332c", "fg": "#eadfd2", "muted": "#b3a393", "accent": "#e0a458",
        "accent_soft": "#4a3a26", "btn": "#b8742d", "btn_hover": "#cc8338", "btn_pressed": "#9a6024",
        "hover": "#312a24", "scroll": "#52473d", "input_bg": "#1e1a17", "selection": "#5a4529",
        "ed_bg": "#1e1a17", "ed_fg": "#eadfd2", "margin_bg": "#26211d", "margin_fg": "#8d7f70",
        "caret": "#fff3e0", "caret_line": "#27221e", "sel_bg": "#5a4529", "sel_fg": "#ffffff",
        "fold_bg": "#26211d", "guide": "#352e27", "edge": "#2d2721",
        "brace_bg": "#4a3d2e", "brace_fg": "#88c0d0", "bad_brace_bg": "#5a2a22", "bad_brace_fg": "#ff7b6b",
        "find_hl": "#7a5f26", "word_hl": "#41362b", "error": "#ef6b5b", "warn": "#ebcb8b", "bookmark": "#e0a458",
        "comment": "#8a9a73", "keyword": "#e0a458", "string": "#a3be8c", "number": "#d08770",
        "type": "#88c0d0", "function": "#ebcb8b", "operator": "#d6c8b8", "decorator": "#b48ead",
        "tag": "#e0a458", "attribute": "#88c0d0", "preprocessor": "#b48ead", "regex": "#d08770",
    },
    "paper": {
        "label": "Paper Warm Light", "dark": False,
        "bg": "#fbf7f0", "panel": "#f1ebe0", "tree": "#fffdf8", "elevated": "#fffdf8",
        "border": "#ddd3c1", "fg": "#3b342b", "muted": "#7a6f60", "accent": "#b5651d",
        "accent_soft": "#f0dcc2", "btn": "#b5651d", "btn_hover": "#c9772c", "btn_pressed": "#97520f",
        "hover": "#ece3d3", "scroll": "#c9bda8", "input_bg": "#fffdf8", "selection": "#ecd5b4",
        "ed_bg": "#fffdf8", "ed_fg": "#3b342b", "margin_bg": "#f4eee2", "margin_fg": "#8f8473",
        "caret": "#3b342b", "caret_line": "#f8f2e6", "sel_bg": "#ecd5b4", "sel_fg": "#2a2118",
        "fold_bg": "#eee6d6", "guide": "#e8dfcd", "edge": "#eee6d6",
        "brace_bg": "#e6d6bb", "brace_fg": "#1d6f8f", "bad_brace_bg": "#f5d3cc", "bad_brace_fg": "#a8321f",
        "find_hl": "#f3dd8a", "word_hl": "#ede0c8", "error": "#b3261e", "warn": "#8a5a00", "bookmark": "#b5651d",
        "comment": "#8a8070", "keyword": "#a23c14", "string": "#3f7d3a", "number": "#1d6f8f",
        "type": "#6b4a9e", "function": "#8a5a00", "operator": "#5a5042", "decorator": "#9a347f",
        "tag": "#a23c14", "attribute": "#1d6f8f", "preprocessor": "#9a347f", "regex": "#3f7d3a",
    },
    "github": {
        "label": "GitHub Theme", "dark": False,
        "bg": "#ffffff", "panel": "#f6f8fa", "tree": "#ffffff", "elevated": "#ffffff",
        "border": "#d0d7de", "fg": "#24292f", "muted": "#57606a", "accent": "#0969da",
        "accent_soft": "#ddf4ff", "btn": "#1f883d", "btn_hover": "#2da44e", "btn_pressed": "#1a7f37",
        "hover": "#f3f4f6", "scroll": "#8c959f", "input_bg": "#ffffff", "selection": "#addcff",
        "ed_bg": "#ffffff", "ed_fg": "#24292f", "margin_bg": "#f6f8fa", "margin_fg": "#8c959f",
        "caret": "#24292f", "caret_line": "#f6f8fa", "sel_bg": "#addcff", "sel_fg": "#24292f",
        "fold_bg": "#f6f8fa", "guide": "#eaeef2", "edge": "#d0d7de",
        "brace_bg": "#ddf4ff", "brace_fg": "#0969da", "bad_brace_bg": "#ffebe9", "bad_brace_fg": "#cf222e",
        "find_hl": "#fff8c5", "word_hl": "#ddf4ff", "error": "#cf222e", "warn": "#9a6700", "bookmark": "#0969da",
        "comment": "#6e7781", "keyword": "#cf222e", "string": "#0a3069", "number": "#0550ae",
        "type": "#953800", "function": "#8250df", "operator": "#24292f", "decorator": "#8250df",
        "tag": "#116329", "attribute": "#0550ae", "preprocessor": "#cf222e", "regex": "#0a3069",
    },
    "eclipse": {
        "label": "Eclipse Theme", "dark": False,
        "bg": "#f4f4f4", "panel": "#e8e8e8", "tree": "#ffffff", "elevated": "#ffffff",
        "border": "#b8b8b8", "fg": "#2a2a2a", "muted": "#666666", "accent": "#2a5db0",
        "accent_soft": "#d4e2fc", "btn": "#3d72b8", "btn_hover": "#4a85d9", "btn_pressed": "#234c8c",
        "hover": "#e0e8f0", "scroll": "#adadad", "input_bg": "#ffffff", "selection": "#c1d5f5",
        "ed_bg": "#ffffff", "ed_fg": "#2a2a2a", "margin_bg": "#eef0f2", "margin_fg": "#787878",
        "caret": "#000000", "caret_line": "#f7f9fa", "sel_bg": "#c1d5f5", "sel_fg": "#000000",
        "fold_bg": "#e8e8e8", "guide": "#e3e3e3", "edge": "#cccccc",
        "brace_bg": "#e2ecfd", "brace_fg": "#0000ff", "bad_brace_bg": "#ffcccc", "bad_brace_fg": "#cc0000",
        "find_hl": "#fff0a0", "word_hl": "#e2ecfd", "error": "#cc0000", "warn": "#b06c00", "bookmark": "#2a5db0",
        "comment": "#3f7f5f", "keyword": "#7f0055", "string": "#2a00ff", "number": "#000000",
        "type": "#000000", "function": "#000000", "operator": "#000000", "decorator": "#7f0055",
        "tag": "#7f0055", "attribute": "#0000c0", "preprocessor": "#7f0055", "regex": "#2a00ff",
    },
    "macos": {
        "label": "Native MacOS Theme", "dark": True,
        "bg": "#1e1e1e", "panel": "#2d2d2d", "tree": "#252525", "elevated": "#333333",
        "border": "#414141", "fg": "#cccccc", "muted": "#888888", "accent": "#007acc",
        "accent_soft": "#1b3c59", "btn": "#0066cc", "btn_hover": "#007acc", "btn_pressed": "#005299",
        "hover": "#383838", "scroll": "#555555", "input_bg": "#252525", "selection": "#264f78",
        "ed_bg": "#1e1e1e", "ed_fg": "#d4d4d4", "margin_bg": "#252525", "margin_fg": "#858585",
        "caret": "#aeafad", "caret_line": "#2a2d2e", "sel_bg": "#264f78", "sel_fg": "#ffffff",
        "fold_bg": "#2d2d2d", "guide": "#333333", "edge": "#333333",
        "brace_bg": "#464646", "brace_fg": "#4ec9b0", "bad_brace_bg": "#5a1d1d", "bad_brace_fg": "#f44747",
        "find_hl": "#623b00", "word_hl": "#2a2d2e", "error": "#f14c4c", "warn": "#cca700", "bookmark": "#007acc",
        "comment": "#6a9955", "keyword": "#c586c0", "string": "#ce9178", "number": "#b5cea8",
        "type": "#4ec9b0", "function": "#dcdcaa", "operator": "#d4d4d4", "decorator": "#c586c0",
        "tag": "#4ec9b0", "attribute": "#9cdcfe", "preprocessor": "#c586c0", "regex": "#d16969",
    },
}

DEFAULT_THEME = "dark"
EDITOR_PALETTES = THEMES

def theme_names():
    return list(THEMES.keys())

def get_theme(name):
    return THEMES.get(name, THEMES[DEFAULT_THEME])

def classify_style(description):
    """Map a QScintilla style description ("Keyword", "Double-quoted string"...) to a palette key.

    Working from the description keeps one theme working across every lexer
    instead of hard-coding style numbers per language.
    """
    d = (description or "").lower()
    if not d or d == "default":
        return "ed_fg"
    if "error" in d or "unclosed" in d or "deleted" in d or "removed" in d:
        return "error"
    if "comment" in d or d.startswith("doc") or "block quote" in d:
        return "comment"
    if "regular expression" in d or "regex" in d:
        return "regex"
    if "preprocessor" in d or "directive" in d or "entity" in d:
        return "preprocessor"
    if "decorator" in d:
        return "decorator"
    if "string" in d or "character" in d or "quote" in d or "heredoc" in d or "here-doc" in d or d == "code" \
            or "inline code" in d or d.startswith("added"):
        return "string"
    if "number" in d or "hex" in d or "list item" in d:
        return "number"
    if "keyword" in d or d.startswith("header") or "strong" in d:
        return "keyword"
    if "class" in d or "type" in d or "namespace" in d:
        return "type"
    if "function" in d or "method" in d or "link" in d or "subroutine" in d:
        return "function"
    if "operator" in d or "rule" in d or "delimiter" in d:
        return "operator"
    if "tag" in d:
        return "tag"
    if "attribute" in d or "property" in d or "key" in d or "variable" in d or "emphasis" in d:
        return "attribute"
    return "ed_fg"
