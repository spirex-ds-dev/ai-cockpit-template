"""Read-only facts gathered before an installer plan is considered."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallationInspection:
    target: Path
    exists: bool
    is_git_repository: bool


def inspect_target(target: Path) -> InstallationInspection:
    """Inspect a target without creating files, directories, or Git state."""

    root = target.resolve()
    return InstallationInspection(
        target=root,
        exists=root.exists(),
        is_git_repository=(root / ".git").exists(),
    )
