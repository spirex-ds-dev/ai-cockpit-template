"""Conflict vocabulary for ownership-aware installer reviews."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Conflict:
    path: str
    classification: str
    detail: str
