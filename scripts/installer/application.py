"""Application service joining read-only inspection and planning."""

from dataclasses import dataclass
from pathlib import Path

from installer.inspection import InstallationInspection, inspect_target
from installer.planning import InstallationPlan


@dataclass(frozen=True)
class InstallationRequest:
    source: Path
    target: Path
    stack: str


@dataclass(frozen=True)
class InstallationApplicationResult:
    inspection: InstallationInspection
    plan: InstallationPlan


class InstallationApplication:
    """Create a read-only domain result before a compatibility installer writes."""

    def inspect_and_plan(self, request: InstallationRequest) -> InstallationApplicationResult:
        inspection = inspect_target(request.target)
        return InstallationApplicationResult(
            inspection=inspection,
            plan=InstallationPlan(target=inspection.target, actions=()),
        )
