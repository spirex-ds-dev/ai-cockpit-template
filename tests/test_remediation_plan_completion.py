from __future__ import annotations

import json
from pathlib import Path

from scripts.check_remediation_plan_completion import audit


def _write_pair(
    root: Path, stem: str, *, readiness: str = "ready_with_risks", align: bool = True
) -> None:
    archive = root / ".ai" / "work-items" / "archive" / "2026"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / f"{stem}.contract.json").write_text(
        json.dumps({"workItemId": stem}), encoding="utf-8"
    )
    summary = {"reviewReadiness": {"status": readiness}, "changedFiles": []}
    if align:
        summary["documentationAlignment"] = {"status": "aligned"}
    (archive / f"{stem}.summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (archive / f"{stem}.archive-manifest.json").write_text(
        json.dumps({"archiveSequence": 1}), encoding="utf-8"
    )


def test_audit_marks_missing_documentation_alignment_and_not_ready(tmp_path):
    _write_pair(tmp_path, "calibration-adopter-evidence", readiness="not_ready", align=False)
    report = audit(tmp_path)
    ids = {finding["id"] for finding in report["findings"]}
    assert "WI-04-NOT-READY" in ids
    assert "WI-04-DOCUMENTATION-ALIGNMENT-MISSING" in ids
    assert report["releaseBlocked"] is True


def test_audit_never_mutates_historical_archives(tmp_path):
    _write_pair(tmp_path, "calibration-adopter-evidence")
    report = audit(tmp_path)
    assert report["historicalArchivesMutated"] is False
