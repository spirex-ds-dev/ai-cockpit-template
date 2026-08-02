"""Evidence vocabulary for an installer transaction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallationEvidence:
    commands: tuple[str, ...]
    results: tuple[str, ...]
    limitations: tuple[str, ...]
