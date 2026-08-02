"""Confirmed execution boundary for installer plans."""

from collections.abc import Callable

from installer.confirmation import Confirmation
from installer.planning import InstallationPlan


class InstallationTransaction:
    """Invoke the supplied transaction executor only after explicit approval."""

    def __init__(self, executor: Callable[[InstallationPlan], None]) -> None:
        self._executor = executor

    def execute(self, plan: InstallationPlan, confirmation: Confirmation) -> None:
        if not confirmation.approved:
            raise PermissionError("installer execution requires explicit confirmation")
        self._executor(plan)
