"""Application settings: defaults, type coercion and validation (no Qt imports)."""

DEFAULTS = {
    # appearance
    "theme": "dark",
    "font_family": "",
    "font_size": 11,
    # editor
    "tab_width": 4,
    "use_tabs": False,
    "word_wrap": False,
    "show_whitespace": False,
    "show_line_numbers": True,
    "show_guides": True,
    "show_edge": True,
    "edge_column": 88,
    "caret_line": True,
    "auto_close": True,
    "highlight_words": True,
    "live_lint": True,
    # files
    "trim_trailing": False,
    "final_newline": False,
    "autosave_seconds": 0,
    "restore_session": True,
    "reload_external": True,
    # running
    "python_path": "",
    "run_timeout": 0,
    "save_before_run": True,
}

EDITOR_KEYS = (
    "font_family", "font_size", "tab_width", "use_tabs", "word_wrap", "show_whitespace",
    "show_line_numbers", "show_guides", "show_edge", "edge_column", "caret_line",
    "auto_close", "highlight_words",
)

LIMITS = {
    "font_size": (7, 40), "tab_width": (1, 16), "edge_column": (40, 200),
    "autosave_seconds": (0, 3600), "run_timeout": (0, 86400),
}


def coerce(key, value):
    """Convert a stored value (QSettings returns strings on some platforms) to its default's type."""
    default = DEFAULTS[key]
    try:
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        if isinstance(default, int):
            number = int(value)
            low, high = LIMITS.get(key, (number, number))
            return max(low, min(high, number))
        return str(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def editor_options(settings):
    return {key: settings.get(key, DEFAULTS[key]) for key in EDITOR_KEYS}
