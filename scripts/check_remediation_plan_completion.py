#!/usr/bin/env python3
"""Audit completion evidence for the comprehensive remediation plan.

The checker is intentionally report-oriented: historical archive records are
immutable, so an incomplete record is surfaced as a finding rather than
rewritten or silently treated as complete.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PLAN_ITEMS: tuple[tuple[str, str], ...] = (
    ("WI-01", "canonical-evidence-foundation"),
    ("WI-02", "unknown-human-confirmation"),
    ("WI-03", "source-mode-install-transaction"),
    ("WI-04", "calibration-adopter-evidence"),
    ("WI-05", "input-trust-prompt-injection"),
    ("WI-06", "absurd-tests-capability-truth"),
    ("WI-07", "lifecycle-state-recovery"),
    ("WI-08", "verification-efficiency-escalation"),
    ("WI-09", "evidence-backed-task-outcome"),
    ("WI-10", "documentation-alignment-20260726"),
    ("WI-11", "enterprise-boundary"),
    ("WI-12", "code-quality-test-architecture"),
    ("WI-13", "deprecated-assets-archive-hygiene"),
    ("WI-14", "cockpit-human-signal-compression"),
    ("WI-15", "full-remediation-acceptance"),
    ("WI-16", "japanese-capability-assessment"),
    ("WI-17", "document_human_agent_trust_layer"),
    ("WI-18", "publish-new-version-20260726"),
    ("WI-19", "clean-execution-plan-documents"),
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def audit(root: Path) -> dict[str, Any]:
    plan_path = (
        root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-25-ai-cockpit-comprehensive-remediation.md"
    )
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""
    archive = root / ".ai" / "work-items" / "archive" / "2026"
    work_items: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []

    for number, stem in PLAN_ITEMS:
        contract_path = archive / f"{stem}.contract.json"
        summary_path = archive / f"{stem}.summary.json"
        manifest_path = archive / f"{stem}.archive-manifest.json"
        summary = _read_json(summary_path)
        contract = _read_json(contract_path)
        manifest = _read_json(manifest_path)
        item: dict[str, Any] = {
            "workItem": number,
            "stem": stem,
            "contract": contract_path.relative_to(root).as_posix()
            if contract_path.is_file()
            else None,
            "summary": summary_path.relative_to(root).as_posix()
            if summary_path.is_file()
            else None,
            "manifest": manifest_path.relative_to(root).as_posix()
            if manifest_path.is_file()
            else None,
            "reviewReadiness": (summary or {}).get("reviewReadiness", {}).get("status"),
            "documentationAlignment": "present"
            if summary is not None and "documentationAlignment" in summary
            else "missing",
            "archiveSequence": (manifest or {}).get("archiveSequence"),
        }

        if summary is None or contract is None:
            findings.append(
                {
                    "id": f"{number}-ARCHIVE-EVIDENCE-MISSING",
                    "severity": "high",
                    "message": "Current plan Work Item does not have the expected archived Contract/Summary pair.",
                }
            )
        if summary is not None and "documentationAlignment" not in summary:
            findings.append(
                {
                    "id": f"{number}-DOCUMENTATION-ALIGNMENT-MISSING",
                    "severity": "high",
                    "message": "Archived Summary does not contain the plan-required documentationAlignment evidence.",
                }
            )
        if item["reviewReadiness"] == "not_ready":
            findings.append(
                {
                    "id": f"{number}-NOT-READY",
                    "severity": "critical",
                    "message": "Archived Summary is explicitly reviewReadiness=not_ready.",
                }
            )
        work_items.append(item)

    wi10 = next(item for item in work_items if item["workItem"] == "WI-10")
    wi10_summary = _read_json(archive / "documentation-alignment-20260726.summary.json") or {}
    changed_paths = {entry.get("path") for entry in wi10_summary.get("changedFiles", [])}
    installation_path = "docs/getting-started/installation.md"
    if installation_path not in changed_paths:
        wi10["installationDocument"] = "not_changed"
        findings.append(
            {
                "id": "WI-10-INSTALLATION-DOCUMENT-MISSING",
                "severity": "high",
                "message": "WI-10 did not change the existing getting-started installation document requested by the user.",
            }
        )
    else:
        wi10["installationDocument"] = "changed"

    wi19 = next(item for item in work_items if item["workItem"] == "WI-19")
    wi18_position = plan_text.find("### WI-18：")
    wi19_position = plan_text.find("### WI-19：")
    explicit_user_order = (
        "WI-19 完成后，才允许执行 WI-18" in plan_text or "WI-19 必须先于 WI-18" in plan_text
    )
    if (
        wi19_position >= 0 and wi18_position >= 0 and wi19_position < wi18_position
    ) or explicit_user_order:
        wi19["currentPlanEvidence"] = "ordered_before_release_pending_completion"
    else:
        wi19["currentPlanEvidence"] = "not_proven"
        findings.append(
            {
                "id": "WI-19-ORDERING-REQUIRES-REVIEW",
                "severity": "high",
                "message": "The current plan must complete WI-19 cleanup before WI-18 publication; the plan still orders publication first.",
            }
        )

    wi16 = next(item for item in work_items if item["workItem"] == "WI-16")
    wi16["japaneseEvidenceBoundary"] = "repository_local_only"
    findings.append(
        {
            "id": "WI-16-JAPANESE-EVIDENCE-BOUNDARY",
            "severity": "high",
            "message": "WI-16 records repository-local deterministic evidence but not human/provider-backed object-engineer interaction evidence.",
        }
    )

    return {
        "schemaVersion": 1,
        "plan": "2026-07-25-ai-cockpit-comprehensive-remediation",
        "workItems": work_items,
        "findings": findings,
        "releaseBlocked": bool(findings),
        "historicalArchivesMutated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"findings": len(report["findings"]), "releaseBlocked": report["releaseBlocked"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
