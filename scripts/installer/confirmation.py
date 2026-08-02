"""Human confirmation required to execute an installer plan."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Confirmation:
    approved: bool
    actor: str
