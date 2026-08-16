"""Reconcile archived Work Item evidence without changing its authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REQUIRED_WORK_ITEMS = (
    "wi-04-cost-metrics-integration",
    "wi-05-outcome-dialog-delivery",
    "wi-06-status-interface",
    "wi-07-evidence-binding-foundation",
    "wi-08-content-bound-reuse-successor",
    "wi-09-diff-bound-reuse",
    "wi-10-environment-bound-reuse-successor",
    "wi-11-governance-profile-effect-successor",
    "wi-12-performance-diagnosis-successor",
    "wi-13-adoption-reality-report",
)
STATUS_COLORS = {
    "completed": "green",
    "completed_with_warnings": "yellow",
    "blocked": "red",
    "failed": "red",
}
OUTCOME_SECTIONS = (
    "outcomeSummary",
    "taskOverview",
    "deliveredChanges",
    "findings",
    "risks",
    "warnings",
    "limitations",
    "nonRiskExplanations",
    "forbiddenClaims",
    "interventions",
    "forcedStops",
    "resolutions",
    "recurrencePrevention",
    "avoidedImpact",
    "residualRisks",
    "humanDecisions",
    "evidence",
)


def _json(path: Path) -> dict[str, Any] | None:
    """Load one JSON object, returning ``None`` for missing or malformed input."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _archive_path(root: Path, task: str, suffix: str) -> Path:
    """Resolve one exact archive artifact without accepting a predecessor variant."""

    archive_root = root / ".ai" / "work-items" / "archive"
    matches = sorted(archive_root.glob(f"*/{task}.{suffix}"))
    return matches[0] if len(matches) == 1 else archive_root / "missing" / f"{task}.{suffix}"


def _expected_color(status: Any) -> str | None:
    return STATUS_COLORS.get(status) if isinstance(status, str) else None


def _item_report(root: Path, task: str) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
    """Validate one archive bundle and return its row plus digest inputs."""

    suffixes = {
        "contract": "contract.json",
        "summary": "summary.json",
        "outcome": "outcome.json",
        "outcomeMarkdown": "outcome.md",
        "manifest": "archive-manifest.json",
    }
    paths = {name: _archive_path(root, task, suffix) for name, suffix in suffixes.items()}
    contract = _json(paths["contract"])
    summary = _json(paths["summary"])
    outcome = _json(paths["outcome"])
    manifest = _json(paths["manifest"])
    findings: list[str] = []
    required_paths: list[str] = []
    for name, path in sorted(paths.items()):
        relative = path.relative_to(root).as_posix()
        required_paths.append(relative)
        if not path.is_file():
            findings.append(f"missing {name} archive artifact")

    for label, value in (("Contract", contract), ("Summary", summary), ("Outcome", outcome)):
        if value is None:
            findings.append(f"malformed {label} JSON")
        elif value.get("workItemId") != task:
            findings.append(f"{label} identity does not match required task")
    if manifest is None:
        findings.append("malformed archive manifest JSON")
    else:
        if manifest.get("workItemId") != task:
            findings.append("manifest identity does not match required task")
        for key, path_key in (("contractPath", "contract"), ("summaryPath", "summary")):
            expected = paths[path_key].relative_to(root).as_posix()
            if manifest.get(key) != expected:
                findings.append(f"manifest {key} does not match archive path")
        for key, path_key in (("contractSha256", "contract"), ("summarySha256", "summary")):
            digest = _sha256(paths[path_key])
            if digest is None or manifest.get(key) != digest:
                findings.append(f"manifest {key} does not match archive bytes")
        artifacts = manifest.get("outcomeArtifacts")
        expected_artifacts = {
            paths["outcome"].relative_to(root).as_posix(): _sha256(paths["outcome"]),
            paths["outcomeMarkdown"].relative_to(root).as_posix(): _sha256(
                paths["outcomeMarkdown"]
            ),
        }
        actual_artifacts = (
            {
                item.get("path"): item.get("sha256")
                for item in artifacts
                if isinstance(item, Mapping)
            }
            if isinstance(artifacts, list)
            else {}
        )
        if actual_artifacts != expected_artifacts:
            findings.append("manifest outcomeArtifacts do not match archive bytes")

    status = outcome.get("status") if outcome else None
    color = outcome.get("humanStatusColor") if outcome else None
    expected_color = _expected_color(status)
    if expected_color is None:
        findings.append(f"unsupported Outcome status: {status}")
    elif color != expected_color:
        findings.append("Outcome humanStatusColor does not match status")

    warnings: list[str] = []
    if isinstance(outcome, Mapping):
        sections = outcome.get("sections")
        if isinstance(sections, Mapping):
            for item in [*sections.get("warnings", []), *sections.get("limitations", [])]:
                if isinstance(item, str) and item:
                    warnings.append(item)
                elif isinstance(item, Mapping):
                    source_warning = item.get("sourceWarning")
                    title = item.get("title")
                    if isinstance(source_warning, str) and source_warning:
                        warnings.append(source_warning)
                    elif isinstance(title, str) and title:
                        warnings.append(title)
    if isinstance(summary, Mapping):
        warnings.extend(str(item) for item in summary.get("knownGaps", []) if item)
        warnings.extend(
            str(item.get("detail"))
            for item in summary.get("residualRisks", [])
            if isinstance(item, Mapping) and item.get("detail")
        )
    row = {
        "taskId": task,
        "outcomeStatus": status or "unknown",
        "humanStatusColor": color or "unknown",
        "archiveLifecycleStage": (
            outcome.get("bindings", {}).get("lifecycleStage", "unknown")
            if isinstance(outcome, Mapping) and isinstance(outcome.get("bindings"), Mapping)
            else "unknown"
        ),
        "archivePullRequestState": (
            outcome.get("bindings", {}).get("pullRequest", {}).get("state", "unknown")
            if isinstance(outcome, Mapping)
            and isinstance(outcome.get("bindings"), Mapping)
            and isinstance(outcome.get("bindings", {}).get("pullRequest"), Mapping)
            else "unknown"
        ),
        "acceptance": "failed" if findings else ("warning" if warnings else "passed"),
        "evidenceState": "invalid" if findings else "valid",
        "archivePaths": required_paths,
        "findings": sorted(set(findings)),
        "limitations": sorted(set(warnings)),
        "outcomeSections": {
            section: outcome.get("sections", {}).get(section, [])
            if isinstance(outcome, Mapping) and isinstance(outcome.get("sections"), Mapping)
            else []
            for section in OUTCOME_SECTIONS
        },
    }
    digest_inputs = []
    for path in paths.values():
        try:
            digest_inputs.append((path.relative_to(root).as_posix(), path.read_bytes()))
        except OSError:
            digest_inputs.append((path.relative_to(root).as_posix(), b"<missing>"))
    return row, digest_inputs


def _source_digest(inputs: list[tuple[str, bytes]]) -> str:
    hasher = hashlib.sha256()
    for path, content in sorted(inputs):
        hasher.update(path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content)
        hasher.update(b"\0")
    return f"sha256:{hasher.hexdigest()}"


def _source_file_state(root: Path, path: str, needles: tuple[str, ...]) -> str:
    try:
        content = (root / path).read_text(encoding="utf-8")
    except OSError:
        return "missing"
    return "verified" if all(needle in content for needle in needles) else "not_verified"


def _outcome_delivery(root: Path) -> dict[str, Any]:
    """Report durable handoff facts separately from unobservable UI receipt."""

    implementation = _source_file_state(
        root,
        "scripts/ai_finish.py",
        ("def deliver_direct_outcome_report", "render_direct_outcome_report"),
    )
    test = _source_file_state(
        root,
        "tests/test_task_outcome_ai_finish_integration.py",
        ("test_blocked_finish_failure_delivers_persisted_outcome_to_conversation",),
    )
    pair = all(
        (root / path).is_file()
        for path in (".ai/cockpit/task_report.json", ".ai/cockpit/task_report.md")
    )
    return {
        "status": "yellow",
        "archiveEvidence": "present",
        "taskReportPair": "present" if pair else "missing",
        "directHandoffImplementation": implementation,
        "directHandoffTest": test,
        "conversationUiReceipt": "not_observable",
        "agentHandoffProtocol": "required_for_every_agent_and_subagent",
        "requiredOutcomeFields": list(OUTCOME_SECTIONS),
        "limitation": "The repository can prove persisted projections and CLI handoff only; a caller may discard or truncate output, and UI receipt is not observable here.",
    }


def _performance_boundary(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize WI-12 evidence without converting diagnosis into an improvement claim."""

    diagnosis_files = all(
        (root / path).is_file()
        for path in (
            ".ai/schemas/performance-diagnosis-report.schema.json",
            "scripts/ai_performance_diagnosis.py",
            "tests/test_ai_performance_diagnosis.py",
            "docs/reference/performance-diagnosis.md",
        )
    )
    wi12 = next(
        (item for item in rows if item["taskId"] == "wi-12-performance-diagnosis-successor"), None
    )
    limitations = list(wi12.get("limitations", [])) if wi12 else ["WI-12 evidence is missing"]
    limitations.append("No comparable before/after baseline is archived for this integration run.")
    return {
        "status": "yellow",
        "diagnosisEvidence": "verified"
        if diagnosis_files and wi12 and wi12["evidenceState"] == "valid"
        else "not_verified",
        "comparableBaseline": "not_provided",
        "runtimeImprovement": "unverified",
        "causalClaim": "forbidden",
        "decisionImpact": "none",
        "limitations": sorted(set(limitations)),
    }


def build_report(root: Path) -> dict[str, Any]:
    """Build a deterministic cross-WI report from immutable repository evidence."""

    rows: list[dict[str, Any]] = []
    digest_inputs: list[tuple[str, bytes]] = []
    for task in REQUIRED_WORK_ITEMS:
        row, inputs = _item_report(root, task)
        rows.append(row)
        digest_inputs.extend(inputs)
    rows.sort(key=lambda item: item["taskId"])
    structural_findings = [
        f"{row['taskId']}: {finding}" for row in rows for finding in row["findings"]
    ]
    outcome_delivery = _outcome_delivery(root)
    performance = _performance_boundary(root, rows)
    for path in (
        "scripts/ai_finish.py",
        "tests/test_task_outcome_ai_finish_integration.py",
        ".ai/cockpit/task_report.json",
        ".ai/cockpit/task_report.md",
        "scripts/ai_performance_diagnosis.py",
        ".ai/schemas/performance-diagnosis-report.schema.json",
    ):
        file_path = root / path
        try:
            digest_inputs.append((path, file_path.read_bytes()))
        except OSError:
            digest_inputs.append((path, b"<missing>"))
    limitations = sorted(
        {
            *[item for row in rows for item in row["limitations"]],
            outcome_delivery["limitation"],
            *performance["limitations"],
        }
    )
    overall = "red" if structural_findings else ("yellow" if limitations else "green")
    return {
        "schemaVersion": 1,
        "reportKind": "cross_wi_integration",
        "overallStatus": overall,
        "decisionImpact": "none",
        "sourceDigest": _source_digest(digest_inputs),
        "requiredWorkItems": sorted(REQUIRED_WORK_ITEMS),
        "workItems": rows,
        "outcomeDelivery": outcome_delivery,
        "performance": performance,
        "limitations": limitations,
        "findings": structural_findings,
        "rerunGuidance": "Rerun after every WI archive or projection change; red requires repairing the exact malformed or mismatched evidence before any merge claim.",
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render the validated report with visible traffic-light status markers."""

    colors = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    status = str(report.get("overallStatus", "red"))
    lines = [
        "# Cross-WI Integration Report",
        "",
        f"Overall: {colors.get(status, '🔴')} `{status}`",
        "",
        "decisionImpact=none (advisory only)",
        "",
        "## Work Item acceptance",
        "",
        "| Work Item | Outcome | Color | Acceptance | Evidence | Archived lifecycle |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.get("workItems", []):
        color = str(row.get("humanStatusColor", "red"))
        lines.append(
            f"| {row.get('taskId', 'unknown')} | {row.get('outcomeStatus', 'unknown')} | "
            f"{colors.get(color, '🔴')} `{color}` | {row.get('acceptance', 'failed')} | "
            f"{row.get('evidenceState', 'invalid')} | {row.get('archiveLifecycleStage', 'unknown')} |"
        )
        sections = row.get("outcomeSections", {})
        if isinstance(sections, Mapping):
            for section in OUTCOME_SECTIONS:
                value = sections.get(section)
                if not value:
                    continue
                label = section.replace("_", " ")
                lines.append(
                    f"  - **{label}**: {json.dumps(value, ensure_ascii=False, sort_keys=True)}"
                )
    delivery = report.get("outcomeDelivery", {})
    lines.extend(
        [
            "",
            "## Outcome dialog delivery",
            "",
            f"- Direct CLI handoff implementation: `{delivery.get('directHandoffImplementation', 'unknown')}`",
            f"- Direct handoff regression test: `{delivery.get('directHandoffTest', 'unknown')}`",
            f"- Conversation UI receipt: `{delivery.get('conversationUiReceipt', 'not_observable')}`",
            f"- Agent/subagent handoff protocol: `{delivery.get('agentHandoffProtocol', 'unknown')}`",
            "- The Outcome report exists; conversation UI receipt is not observable from repository files alone.",
            "",
            "## Performance acceptance",
            "",
            f"- Diagnosis evidence: `{report.get('performance', {}).get('diagnosisEvidence', 'unknown')}`",
            f"- Comparable baseline: `{report.get('performance', {}).get('comparableBaseline', 'unknown')}`",
            "- runtime performance improvement is unverified; no causal claim is made.",
            "",
            "## Limitations",
            "",
        ]
    )
    limitations = report.get("limitations", [])
    lines.extend(f"- {item}" for item in limitations if isinstance(item, str))
    lines.extend(["", str(report.get("rerunGuidance", "")), ""])
    return "\n".join(lines)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(f"cross-WI integration report: {report['overallStatus']}")
    return 2 if report["overallStatus"] == "red" else 0


if __name__ == "__main__":
    raise SystemExit(_main())
