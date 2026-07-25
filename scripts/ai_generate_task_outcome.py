"""Generate an evidence-derived Task Outcome JSON and Markdown view.

The generator is intentionally a small, deterministic transformation. It does
not validate schema bindings; the validator Work Item owns that responsibility.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


GENERATOR_VERSION = "1.0"
FINAL_STATUSES = {
    "completed",
    "completed_with_warnings",
    "needs_human_confirmation",
    "blocked",
    "cancelled",
}
SECTION_TITLES = {
    "outcomeSummary": "Outcome Summary",
    "taskOverview": "Task Overview",
    "deliveredChanges": "Delivered Changes",
    "findings": "Findings",
    "risks": "Risks",
    "warnings": "Warnings",
    "interventions": "Interventions",
    "forcedStops": "Forced Stops",
    "resolutions": "Resolutions",
    "recurrencePrevention": "Recurrence Prevention",
    "avoidedImpact": "Avoided Impact",
    "residualRisks": "Residual Risks",
    "humanDecisions": "Human Decisions",
    "evidence": "Evidence",
}
SECRET_KEY = re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.I)


def _safe_text(value: Any, default: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _evidence_refs(value: Any, fallback: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            source = _safe_text(item.get("source"), fallback)
            subject = _safe_text(item.get("subject"), "evidence")
            ref = {"source": source, "subject": subject}
            digest = item.get("digest")
            if isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest):
                ref["digest"] = digest
            refs.append(ref)
        elif isinstance(item, str) and item.strip():
            refs.append({"source": fallback, "subject": item.strip()})
    return refs


def _event_sort_key(event: Mapping[str, Any]) -> tuple[str, str]:
    return (_safe_text(event.get("occurredAt")), _safe_text(event.get("eventId")))


def _event_description(event: Mapping[str, Any]) -> str:
    for key in ("description", "message", "reason", "title", "decision"):
        text = _safe_text(event.get(key))
        if text:
            return text
    return _safe_text(event.get("eventType"), "event")


def _state(event: Mapping[str, Any], default: str = "unresolved") -> str:
    value = _safe_text(event.get("state"), default)
    return (
        value
        if value in {"resolved", "mitigated", "accepted", "unresolved", "not_applicable"}
        else default
    )


def _risk(event: Mapping[str, Any], *, accepted: bool = False) -> dict[str, Any]:
    kind = _safe_text(event.get("kind"), "potential_risk")
    if kind not in {"observed_problem", "potential_risk", "prevented_event"}:
        kind = "potential_risk"
    severity = _safe_text(event.get("severity"), "medium")
    if severity not in {"informational", "low", "medium", "high", "critical"}:
        severity = "medium"
    return {
        "kind": kind,
        "severity": severity,
        "title": _safe_text(event.get("title"), _event_description(event)),
        "state": "accepted" if accepted else _state(event),
        "description": _event_description(event),
        "evidence": _evidence_refs(event.get("evidence"), "task-event-log"),
    }


def _conditional_impact(value: Any) -> str | None:
    impact = _safe_text(value)
    if not impact:
        return None
    if impact.lower().startswith(("if not detected", "could have", "如果未被发现")):
        return impact.rstrip(".") + "."
    return f"If not detected, could have led to {impact.rstrip('.')}."


def _status(
    evidence: Mapping[str, Any], events: Sequence[Mapping[str, Any]], warnings: list[str]
) -> str:
    requested = _safe_text(evidence.get("status"))
    if requested in FINAL_STATUSES:
        return requested
    types = {event.get("eventType") for event in events}
    if "cancelled" in types:
        return "cancelled"
    if "stop" in types:
        return "needs_human_confirmation"
    return "completed_with_warnings" if warnings else "completed"


def generate_outcome(
    task_id: str,
    bindings: Mapping[str, Any],
    *,
    events: Sequence[Mapping[str, Any]] = (),
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic Outcome object from structured evidence/events."""

    evidence = evidence or {}
    ordered = sorted((dict(event) for event in events), key=_event_sort_key)
    findings: list[dict[str, Any]] = []
    finding_keys: set[str] = set()
    risks: list[dict[str, Any]] = []
    warnings: list[str] = [
        item.strip()
        for item in evidence.get("warnings", [])
        if isinstance(item, str) and item.strip()
    ]
    interventions: list[dict[str, Any]] = []
    forced_stops: list[dict[str, Any]] = []
    resolutions: list[dict[str, Any]] = []
    prevention: list[dict[str, Any]] = []
    avoided: list[str] = []
    human_decisions: list[str] = [
        item.strip()
        for item in evidence.get("humanDecisions", [])
        if isinstance(item, str) and item.strip()
    ]
    all_evidence: list[dict[str, str]] = _evidence_refs(
        evidence.get("evidence"), "structured-evidence"
    )
    all_evidence.extend(_evidence_refs(evidence.get("sources"), "structured-evidence"))
    publication = evidence.get("publication")
    if isinstance(publication, dict):
        tag = _safe_text(publication.get("tag"), "published-release")
        digest = publication.get("assetDigest")
        ref = {
            "source": "release-workflow",
            "subject": tag,
        }
        if isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest):
            ref["digest"] = digest
        all_evidence.append(ref)

    for event in ordered:
        event_type = event.get("eventType")
        refs = _evidence_refs(event.get("evidence"), "task-event-log")
        all_evidence.extend(refs)
        if event_type == "finding":
            fingerprint = _safe_text(
                event.get("findingFingerprint"), _safe_text(event.get("eventId"), "finding")
            )
            key = (
                fingerprint
                if event.get("recurrence") != "post_fix"
                else f"{fingerprint}:{event.get('eventId')}"
            )
            if key in finding_keys:
                continue
            finding_keys.add(key)
            category = _safe_text(event.get("category"), "other")
            if category not in {
                "gap",
                "defect",
                "evidence",
                "security",
                "installer",
                "release",
                "process",
                "other",
            }:
                category = "other"
            severity = _safe_text(event.get("severity"), "medium")
            if severity not in {"informational", "low", "medium", "high", "critical"}:
                severity = "medium"
            findings.append(
                {
                    "findingFingerprint": fingerprint,
                    "category": category,
                    "severity": severity,
                    "title": _safe_text(event.get("title"), _event_description(event)),
                    "state": _state(event),
                    "description": _event_description(event),
                    "evidence": refs,
                }
            )
        elif event_type == "risk":
            risks.append(_risk(event))
        elif event_type == "risk-accepted":
            risks.append(_risk(event, accepted=True))
        elif event_type == "warning":
            warnings.append(_event_description(event))
        elif event_type in {"confirmation", "resume"}:
            decision = _safe_text(event.get("decision"), _event_description(event))
            if decision:
                human_decisions.append(decision)
        elif event_type == "stop":
            forced_stops.append(
                {
                    "stage": _safe_text(event.get("stage"), "unknown"),
                    "reason": _safe_text(event.get("reason"), _event_description(event)),
                    "policyOrGuard": _safe_text(event.get("policyOrGuard"), "governance guard"),
                    "attemptedAction": _safe_text(
                        event.get("attemptedAction"), "continue execution"
                    ),
                    "conditionalImpact": _safe_text(
                        _conditional_impact(event.get("avoidedImpact"))
                    ),
                    "handoff": _safe_text(event.get("handoff")),
                    "humanDecision": _safe_text(event.get("humanDecision")),
                    "recovery": _safe_text(event.get("recovery")),
                    "result": _state(event),
                    "evidence": refs,
                }
            )
        elif event_type == "resolution":
            resolutions.append(
                {
                    "problem": _safe_text(event.get("problem"), _event_description(event)),
                    "action": _safe_text(event.get("action"), "Recorded corrective action"),
                    "verification": _safe_text(event.get("verification"), "Evidence review"),
                    "result": _state(event, "resolved"),
                    "evidence": refs,
                }
            )
        elif event_type == "prevention":
            kind = _safe_text(event.get("kind"), "None")
            if kind not in {
                "None",
                "Documentation",
                "Test",
                "Automated Check",
                "Structural Prevention",
            }:
                kind = "None"
            prevention.append(
                {
                    "kind": kind,
                    "coverage": _safe_text(event.get("coverage"), "No coverage claim recorded"),
                    "limits": _safe_text(event.get("limits")),
                    "humanDependency": _safe_text(
                        event.get("humanDependency"), "Human review remains required"
                    ),
                }
            )
        if event_type in {"stop", "intervention", "risk", "resolution"}:
            impact = _conditional_impact(event.get("avoidedImpact"))
            if impact and refs:
                avoided.append(impact)
        if event_type == "intervention":
            kind = _safe_text(event.get("kind"), "observed")
            if kind not in {"observed", "warned", "intervened", "prevented"}:
                kind = "observed"
            interventions.append(
                {
                    "kind": kind,
                    "title": _safe_text(event.get("title"), _event_description(event)),
                    "description": _event_description(event),
                    "evidence": refs,
                }
            )

    def unique_refs(refs: list[dict[str, str]]) -> list[dict[str, str]]:
        return list({json.dumps(ref, sort_keys=True): ref for ref in refs}.values())

    status = _status(evidence, ordered, warnings)
    residual = [risk for risk in risks if risk["state"] in {"accepted", "unresolved"}]
    delivered = [
        item
        for item in evidence.get("deliveredChanges", evidence.get("changedFiles", []))
        if isinstance(item, str)
    ]
    sections: dict[str, Any] = {
        "outcomeSummary": _safe_text(
            evidence.get("outcomeSummary"),
            f"Task {task_id} generated an evidence-derived outcome with status {status}.",
        ),
        "taskOverview": _safe_text(evidence.get("taskOverview"), f"Governed Work Item: {task_id}"),
        "deliveredChanges": delivered,
        "findings": findings,
        "risks": risks,
        "warnings": sorted(set(warnings)),
        "interventions": interventions,
        "forcedStops": forced_stops,
        "resolutions": resolutions,
        "recurrencePrevention": prevention,
        "avoidedImpact": sorted(set(avoided)),
        "residualRisks": residual,
        "humanDecisions": human_decisions,
        "evidence": unique_refs(all_evidence),
    }
    return {
        "format": "ai-cockpit-task-outcome",
        "schemaVersion": 1,
        "workItemId": task_id,
        "status": status,
        "bindings": dict(bindings),
        "sections": sections,
    }


def render_markdown(outcome: Mapping[str, Any]) -> str:
    """Render Markdown as a derived view; empty sections are explicitly None."""

    sections = outcome["sections"]
    lines = [f"# Task Outcome: {outcome['workItemId']}", "", f"Status: `{outcome['status']}`", ""]
    for key, title in SECTION_TITLES.items():
        lines.extend([f"## {title}"])
        value = sections[key]
        if isinstance(value, list):
            if not value:
                lines.append("None")
            else:
                for item in value:
                    if isinstance(item, dict):
                        lines.append(
                            f"- {item.get('title', item.get('subject', item.get('kind', json.dumps(item, sort_keys=True))))}"
                        )
                    else:
                        lines.append(f"- {item}")
        else:
            lines.append(value or "None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="Evidence JSON containing taskId, bindings, events, and optional evidence",
    )
    parser.add_argument("json_output", type=Path)
    parser.add_argument("markdown_output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = generate_outcome(
        payload["taskId"],
        payload["bindings"],
        events=payload.get("events", []),
        evidence=payload.get("evidence"),
    )
    args.json_output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
