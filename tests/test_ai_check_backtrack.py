"""Regression coverage for authorized Work Item evidence cleanup."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import ai_check_backtrack as backtrack


def test_authorized_work_item_record_deletion_is_not_reported() -> None:
    changes = [
        (
            "D",
            ".ai/work-items/active/documentation-current-revision-reader-validation.receipt.json",
        )
    ]

    assert (
        backtrack.detect_items(
            changes,
            authorized_deletions={changes[0][1]},
        )
        == []
    )


def test_unapproved_work_item_record_deletion_remains_fail_closed() -> None:
    path = ".ai/work-items/active/unapproved.receipt.json"

    findings = backtrack.detect_items([("D", path)], authorized_deletions=set())

    assert len(findings) == 1
    assert findings[0].kind == "removed_work_item_record"
    assert findings[0].path == path


def test_authorization_requires_approved_policy_and_summary_entry(monkeypatch, tmp_path) -> None:
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    contract_path = active / "cleanup.contract.json"
    summary_path = active / "cleanup.summary.json"
    target = ".ai/work-items/active/closed.receipt.json"
    contract_path.write_text(
        '{"workItemId":"cleanup","destructiveChangePolicy":'
        '{"allowed":true,"allowPatterns":[".ai/work-items/active/closed.*.json"],'
        '"approvalEvidence":{"approved":true}}}',
        encoding="utf-8",
    )
    summary_path.write_text(
        '{"destructiveChanges":[{"path":"' + target + '","action":"delete"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)

    assert backtrack.authorized_deletion_paths() == {target}


def test_authorization_requires_matching_contract_and_summary(monkeypatch, tmp_path) -> None:
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    (active / "cleanup.contract.json").write_text("{}", encoding="utf-8")
    (active / "other.summary.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)

    assert backtrack.authorized_deletion_paths() == set()


def test_authorization_fails_closed_for_invalid_policy_shapes(monkeypatch, tmp_path) -> None:
    active = tmp_path / ".ai" / "work-items" / "active"
    active.mkdir(parents=True)
    contract_path = active / "cleanup.contract.json"
    summary_path = active / "cleanup.summary.json"
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)

    summary_path.write_text('{"destructiveChanges": []}', encoding="utf-8")
    contract_path.write_text("{", encoding="utf-8")
    assert backtrack.authorized_deletion_paths() == set()

    cases = [
        {},
        {"destructiveChangePolicy": {"allowed": True}},
        {
            "destructiveChangePolicy": {
                "allowed": True,
                "approvalEvidence": {"approved": True},
                "allowPatterns": [".ai/**", 1],
            }
        },
    ]
    for payload in cases:
        contract_path.write_text(json.dumps(payload), encoding="utf-8")
        assert backtrack.authorized_deletion_paths() == set()

    contract_path.write_text(
        json.dumps(
            {
                "destructiveChangePolicy": {
                    "allowed": True,
                    "approvalEvidence": {"approved": True},
                    "allowPatterns": [".ai/work-items/active/*.json"],
                }
            }
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        '{"destructiveChanges": [{}, {"path": 1}, '
        '{"path": ".ai/work-items/active/closed.json", "action": "keep"}, '
        '{"path": ".ai/work-items/active/closed.json", "action": "delete"}]}',
        encoding="utf-8",
    )
    assert backtrack.authorized_deletion_paths() == {".ai/work-items/active/closed.json"}


def test_detect_items_reports_snapshots_and_defaults_to_fail_closed() -> None:
    findings = backtrack.detect_items(
        [
            ("D", "tests/removed_test.py"),
            ("D", "fixtures/example.snapshot"),
            ("D", ".ai/work-items/active/removed.receipt.json"),
        ]
    )

    assert [finding.kind for finding in findings] == [
        "deleted_test",
        "deleted_snapshot",
        "removed_work_item_record",
    ]


def test_parse_args_accepts_verbose(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ai_check_backtrack.py", "--verbose"])

    assert backtrack.parse_args().verbose is True


def test_main_reports_no_issues_and_passes_observability(monkeypatch, tmp_path) -> None:
    report = tmp_path / "target" / "backtrack.json"
    policy = tmp_path / "policy.yaml"
    policy.write_text("reportOnly: true\n", encoding="utf-8")
    events: list[str] = []
    observer = SimpleNamespace(
        guard_violation=lambda **_kwargs: events.append("guard"),
        check_failed=lambda **_kwargs: events.append("failed"),
        check_passed=lambda **_kwargs: events.append("passed"),
    )
    monkeypatch.setattr(backtrack, "REPORT_PATH", report)
    monkeypatch.setattr(backtrack, "POLICY_PATH", policy)
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backtrack, "changed_name_status", list)
    monkeypatch.setattr(backtrack, "authorized_deletion_paths", lambda: set())
    monkeypatch.setattr(backtrack, "create_observability", lambda: observer)
    monkeypatch.setattr(backtrack, "parse_args", lambda: SimpleNamespace(verbose=False))

    assert backtrack.main() == 0
    assert events == ["passed"]
    assert report.exists()


def test_main_reports_report_only_findings(monkeypatch, tmp_path) -> None:
    report = tmp_path / "target" / "backtrack.json"
    policy = tmp_path / "policy.yaml"
    policy.write_text("reportOnly: true\n", encoding="utf-8")
    events: list[str] = []
    observer = SimpleNamespace(
        guard_violation=lambda **_kwargs: events.append("guard"),
        check_failed=lambda **_kwargs: events.append("failed"),
        check_passed=lambda **_kwargs: events.append("passed"),
    )
    monkeypatch.setattr(backtrack, "REPORT_PATH", report)
    monkeypatch.setattr(backtrack, "POLICY_PATH", policy)
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backtrack, "changed_name_status", lambda: [("D", "a.snap")])
    monkeypatch.setattr(backtrack, "authorized_deletion_paths", lambda: set())
    monkeypatch.setattr(backtrack, "create_observability", lambda: observer)
    monkeypatch.setattr(backtrack, "parse_args", lambda: SimpleNamespace(verbose=True))

    assert backtrack.main() == 0
    assert events == ["guard", "passed"]


def test_main_blocks_findings_when_policy_is_not_report_only(monkeypatch, tmp_path) -> None:
    report = tmp_path / "target" / "backtrack.json"
    policy = tmp_path / "policy.yaml"
    policy.write_text("reportOnly: false\n", encoding="utf-8")
    events: list[str] = []
    observer = SimpleNamespace(
        guard_violation=lambda **_kwargs: events.append("guard"),
        check_failed=lambda **_kwargs: events.append("failed"),
        check_passed=lambda **_kwargs: events.append("passed"),
    )
    monkeypatch.setattr(backtrack, "REPORT_PATH", report)
    monkeypatch.setattr(backtrack, "POLICY_PATH", policy)
    monkeypatch.setattr(backtrack, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backtrack, "changed_name_status", lambda: [("D", "a.snap")])
    monkeypatch.setattr(backtrack, "authorized_deletion_paths", lambda: set())
    monkeypatch.setattr(backtrack, "create_observability", lambda: observer)
    monkeypatch.setattr(backtrack, "parse_args", lambda: SimpleNamespace(verbose=False))

    assert backtrack.main() == 1
    assert events == ["guard", "failed"]


def test_main_fails_closed_when_change_discovery_errors(monkeypatch) -> None:
    monkeypatch.setattr(backtrack, "parse_args", lambda: SimpleNamespace(verbose=False))

    def fail() -> list[tuple[str, str]]:
        raise RuntimeError("git unavailable")

    monkeypatch.setattr(backtrack, "changed_name_status", fail)

    assert backtrack.main() == 1
