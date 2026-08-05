"""Shared isolated-repository fixture construction.

Fixture copies contain tracked source inputs only.  Git metadata, retained linked
worktrees, and local build/cache outputs are runtime state and never belong in
an isolated repository verification fixture.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

RUNTIME_ONLY_PATTERNS = (
    ".git",
    ".venv",
    ".worktrees",
    "target",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "*.pyc",
)


def copy_repository_tree(
    source: Path,
    destination: Path,
    *,
    copy_function: Callable[..., object] = shutil.copy2,
) -> None:
    """Copy repository source while excluding retained local runtime state."""
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*RUNTIME_ONLY_PATTERNS),
        copy_function=copy_function,
    )
