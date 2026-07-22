"""Evidence model for executable lifecycle fixture runs."""

from __future__ import annotations

from typing import Any


def classify_run(
    stack: str, phases: list[str], toolchain_available: bool, simulated: bool = False
) -> dict[str, Any]:
    """Classify evidence without claiming unavailable tools executed."""
    if simulated:
        kind = "simulation"
    elif not toolchain_available:
        kind = "not_run"
    else:
        kind = "local_real_execution"
    return {
        "stack": stack,
        "evidenceKind": kind,
        "phases": list(phases) if kind != "not_run" else [],
        "requiredResume": "install toolchain and rerun" if kind == "not_run" else None,
    }
