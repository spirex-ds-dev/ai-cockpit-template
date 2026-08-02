"""Rollback result vocabulary independent of installer presentation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RollbackResult:
    restored_paths: tuple[str, ...]
    remaining_paths: tuple[str, ...]
    complete: bool
