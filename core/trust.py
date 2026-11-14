"""Workspace Trust (like VS Code): plugins only run from folders the user explicitly trusted.

Pure Python (no Qt) so it can be unit-tested headlessly.
"""
import os


def normalize(path):
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def is_trusted(trusted_paths, workspace):
    """True if ``workspace`` itself is in the trusted list (parents are NOT inherited)."""
    target = normalize(workspace)
    return any(normalize(p) == target for p in trusted_paths or [])


def with_trusted(trusted_paths, workspace):
    result = [p for p in (trusted_paths or []) if isinstance(p, str) and p]
    if not is_trusted(result, workspace):
        result.append(os.path.abspath(workspace))
    return result


def without_trusted(trusted_paths, workspace):
    target = normalize(workspace)
    return [p for p in (trusted_paths or []) if isinstance(p, str) and p and normalize(p) != target]


def is_too_broad(workspace):
    """Home folder and drive/filesystem roots must never be trusted as a whole."""
    path = normalize(workspace)
    home = normalize(os.path.expanduser("~"))
    return path == home or os.path.dirname(path) == path
