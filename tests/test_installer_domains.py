from __future__ import annotations

from pathlib import Path

import pytest
from installer.application import InstallationApplication, InstallationRequest
from installer.confirmation import Confirmation
from installer.planning import InstallationPlan
from installer.transaction import InstallationTransaction


def test_application_inspection_and_planning_are_read_only(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "README.md").write_text("project\n", encoding="utf-8")
    before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))

    application = InstallationApplication()
    result = application.inspect_and_plan(
        InstallationRequest(source=tmp_path / "source", target=target, stack="generic")
    )

    assert result.inspection.target == target.resolve()
    assert result.plan.actions == ()
    assert sorted(path.relative_to(target).as_posix() for path in target.rglob("*")) == before


def test_transaction_rejects_unconfirmed_plan_before_executor_runs(tmp_path: Path) -> None:
    invoked = False

    def executor(_plan: InstallationPlan) -> None:
        nonlocal invoked
        invoked = True

    transaction = InstallationTransaction(executor)
    plan = InstallationPlan(target=tmp_path, actions=())

    with pytest.raises(PermissionError, match="explicit confirmation"):
        transaction.execute(plan, Confirmation(approved=False, actor="operator"))

    assert invoked is False


def test_public_domains_expose_required_review_objects() -> None:
    from installer.evidence import InstallationEvidence
    from installer.inspection import InstallationInspection
    from installer.ownership import Conflict
    from installer.rollback import RollbackResult

    assert InstallationInspection.__name__ == "InstallationInspection"
    assert Conflict.__name__ == "Conflict"
    assert RollbackResult.__name__ == "RollbackResult"
    assert InstallationEvidence.__name__ == "InstallationEvidence"


def test_compatibility_cli_is_a_thin_non_writing_adapter() -> None:
    entrypoint = (
        Path(__file__).resolve().parents[1] / "scripts" / "install_ai_cockpit.py"
    ).read_text(encoding="utf-8")

    assert "class Installer" not in entrypoint
    assert ".write_text(" not in entrypoint
    assert "from installer.application import" in entrypoint
