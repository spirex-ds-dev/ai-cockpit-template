#!/usr/bin/env python3
"""Build a conservative, repository-local adoption reality report.

The report deliberately keeps template capability truth separate from adopter
and provider evidence.  It is a presentation/validation boundary, not an
adoption readiness gate and not a provider-state client.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_OWNED_PREFIXES = (".ai/cockpit/", "templates/")
TEMPLATE_STATUSES = {"implemented", "template_only", "adopter_installed", "planned"}
ADOPTER_STATES = {"verified", "not_configured", "unknown", "external_responsibility"}
CONTROL_IDS = [
    "installation",
    "calibration",
    "hosted_ci",
    "branch_protection",
    "external_identity",
    "codeql",
    "sbom",
    "provenance",
    "signing",
    "production_sandbox",
]


def _as_evidence(value: object) -> list[str]:
    if not isinstance(value, list):
        raise TypeError("adopter evidence must be a list of paths")
    evidence = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(evidence) != len(value):
        raise ValueError("adopter evidence paths must be non-empty strings")
    for path in evidence:
        if path.startswith(TEMPLATE_OWNED_PREFIXES):
            raise ValueError(f"template-owned evidence cannot verify adopter state: {path}")
    return evidence


def _template_rows(rows: object) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError("template capability rows must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("template capability rows must contain objects")
        identifier = str(row.get("id", "")).strip()
        status = str(row.get("status", "")).strip()
        if not identifier or identifier in seen:
            raise ValueError("template capability row ids must be non-empty and unique")
        if status not in TEMPLATE_STATUSES:
            raise ValueError(f"unsupported template capability status: {status}")
        seen.add(identifier)
        normalized.append(
            {
                "id": identifier,
                "status": status,
                "claim": str(row.get("claim", "")).strip(),
            }
        )
    return normalized


def build_report(
    template_rows: list[dict[str, object]],
    adopter_controls: Mapping[str, Mapping[str, object]],
) -> dict[str, Any]:
    """Build a deterministic report from template and explicitly supplied facts."""
    if not isinstance(adopter_controls, Mapping):
        raise TypeError("adopter controls must be an object")
    unknown_controls = sorted(set(adopter_controls) - set(CONTROL_IDS))
    if unknown_controls:
        raise ValueError(f"unknown adopter control: {unknown_controls[0]}")

    controls: list[dict[str, Any]] = []
    for identifier in CONTROL_IDS:
        supplied = adopter_controls.get(identifier, {})
        if not isinstance(supplied, Mapping):
            raise TypeError(f"adopter control must be an object: {identifier}")
        state = str(supplied.get("state", "not_configured")).strip()
        if state not in ADOPTER_STATES:
            raise ValueError(f"unsupported adopter state for {identifier}: {state}")
        evidence = _as_evidence(supplied.get("evidence", []))
        if state == "verified" and not evidence:
            raise ValueError(f"verified adopter control requires evidence: {identifier}")
        item: dict[str, Any] = {"id": identifier, "state": state, "evidence": evidence}
        for key in ("owner", "reason", "verifiedAt"):
            value = supplied.get(key)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{key} must be a non-empty string: {identifier}")
                item[key] = value.strip()
        if (
            state in {"unknown", "not_configured", "external_responsibility"}
            and "reason" not in item
        ):
            item["reason"] = {
                "not_configured": "No adopter evidence was supplied.",
                "unknown": "Current evidence is insufficient to classify this control.",
                "external_responsibility": "The provider or adopter-owned system must supply this evidence.",
            }[state]
        controls.append(item)

    return {
        "schemaVersion": 1,
        "reportKind": "adoption_reality",
        "boundary": "Repository-local template facts do not prove adopter or provider state.",
        "templateCapabilityTruth": {
            "source": "docs/reference/capability-truth-matrix.json",
            "rows": _template_rows(template_rows),
        },
        "adopterVerification": {
            "controls": controls,
            "evidenceRule": "verified requires explicit non-template-owned adopter evidence.",
        },
        "readinessClaim": "not_claimed",
        "limitations": [
            "This report does not inspect hosted CI, branch protection, external identity, or production systems.",
            "CodeQL, SBOM, provenance, signing, and sandbox controls require adopter or provider evidence.",
            "Outcome/task_report remain the governed delivery projections; this report is not a replacement authority.",
        ],
    }


def validate_report(report: Mapping[str, Any]) -> list[str]:
    """Return fail-closed structural and boundary issues without mutating input."""
    issues: list[str] = []
    if report.get("schemaVersion") != 1:
        issues.append("unsupported report schemaVersion")
    if report.get("reportKind") != "adoption_reality":
        issues.append("reportKind must be adoption_reality")
    template = report.get("templateCapabilityTruth")
    if not isinstance(template, Mapping):
        issues.append("templateCapabilityTruth must be an object")
    else:
        try:
            _template_rows(template.get("rows"))
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))
    section = report.get("adopterVerification")
    controls = section.get("controls") if isinstance(section, Mapping) else None
    if not isinstance(controls, list):
        issues.append("adopterVerification.controls must be a list")
        controls = []
    seen: set[str] = set()
    for item in controls:
        if not isinstance(item, Mapping):
            issues.append("adopter control must be an object")
            continue
        identifier = str(item.get("id", ""))
        state = str(item.get("state", ""))
        if identifier not in CONTROL_IDS or identifier in seen:
            issues.append(f"unknown control: {identifier}")
        seen.add(identifier)
        if state not in ADOPTER_STATES:
            issues.append(f"unsupported adopter state: {state}")
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            issues.append(f"evidence must be a list: {identifier}")
            continue
        if state == "verified" and not evidence:
            issues.append(f"verified control lacks evidence: {identifier}")
        for path in evidence:
            if not isinstance(path, str) or not path.strip():
                issues.append(f"evidence path is malformed: {identifier}")
            elif path.startswith(TEMPLATE_OWNED_PREFIXES):
                issues.append(f"template-owned evidence cannot verify adopter state: {path}")
    if {item.get("id") for item in controls if isinstance(item, Mapping)} != set(CONTROL_IDS):
        issues.append("adopter controls must contain exactly the declared control ids")
    if report.get("readinessClaim") != "not_claimed":
        issues.append("readinessClaim must remain not_claimed")
    return issues


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render the validated report as stable human-readable Markdown."""
    issues = validate_report(report)
    if issues:
        raise ValueError("cannot render invalid adoption report: " + "; ".join(issues))
    lines = [
        "# Adoption Reality Report",
        "",
        "This report separates template capability truth from adopter and provider evidence.",
        "Readiness is intentionally **not claimed** by this report.",
        "",
        "## Template capability truth",
        "",
        "| ID | Template state | Claim |",
        "| --- | --- | --- |",
    ]
    rows = report["templateCapabilityTruth"]["rows"]
    for row in rows:
        lines.append(f"| {row['id']} | {row['status']} | {row['claim'] or 'None'} |")
    lines.extend(
        [
            "",
            "## Adopter verification",
            "",
            "| Control | State | Evidence | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in report["adopterVerification"]["controls"]:
        evidence = ", ".join(item["evidence"]) or "None"
        lines.append(
            f"| {item['id']} | {item['state']} | {evidence} | {item.get('reason', 'None')} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- `verified` requires an explicit, non-template-owned adopter evidence reference.",
            "- `unknown` and `not_configured` are not passes.",
            "- `external_responsibility` means the adopter or provider must supply the evidence.",
            "- Production sandbox, hosted CI, branch protection, external identity, CodeQL, SBOM, provenance, and signing are not proven by this template checkout.",
            "",
        ]
    )
    return "\n".join(lines)


def repository_template_rows(root: Path) -> list[dict[str, object]]:
    path = root / "docs" / "reference" / "capability-truth-matrix.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("capabilities") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise TypeError("capability truth matrix has no capabilities list")
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def write_repository_report(root: Path, output: Path, markdown_output: Path) -> dict[str, Any]:
    report = build_report(repository_template_rows(root), {})
    if validate_report(report):
        raise ValueError("generated adoption report did not validate")
    output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "target" / "adoption-reality-report.json"
    )
    parser.add_argument(
        "--markdown-output", type=Path, default=ROOT / "target" / "adoption-reality-report.md"
    )
    args = parser.parse_args()
    try:
        report = write_repository_report(args.root.resolve(), args.output, args.markdown_output)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"adoption reality report failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"status": "not_claimed", "controls": len(report["adopterVerification"]["controls"])},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
