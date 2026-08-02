"""Read-only installer plans."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallationPlan:
    """An immutable list of proposed actions for one target repository."""

    target: Path
    actions: tuple[str, ...]
