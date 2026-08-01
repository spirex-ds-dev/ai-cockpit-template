"""Fail-closed validation for Task Outcome JSON and derived Markdown."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

STATUSES = {
    "completed",
    "completed_with_warnings",
    "needs_human_confirmation",
    "blocked",
    "cancelled",
}
SEVERITIES = {"informational", "low", "medium", "high", "critical"}
SECTIONS = {
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
}
LEGACY_SECTIONS = SECTIONS - {"limitations", "nonRiskExplanations", "forbiddenClaims"}
SECRET_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key)", re.IGNORECASE
)
UNSUPPORTED_KEY = re.compile(
    r"(score|hours?|money|percentage|percent|productivity|savings)", re.IGNORECASE
)
CONDITIONAL = ("if not detected", "could have", "如果未被发现", "可能导致")
NOT_RUN = re.compile(r"\bnot[_ -]?run\b", re.IGNORECASE)
INCOMPATIBLE_VERIFIED_CLAIM = re.compile(
    r"\b(?:enterprise[-_ ]ready|platform[-_ ]verified)\b", re.IGNORECASE
)
# Work Item Contracts historically use both hyphenated and underscore task IDs
# (for example, the installed first-adoption Contract is adopt_ai_cockpit).
# Outcome validation must bind that canonical Contract ID rather than reject a
# valid lifecycle purely because its separator differs.
TASK_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,127}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: tuple[ValidationError, ...]


def _error(errors: list[ValidationError], code: str, message: str) -> None:
    errors.append(ValidationError(code, message))


def _walk(value: Any, errors: list[ValidationError], path: str = "outcome") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_KEY.search(str(key)):
                _error(errors, "privacy", f"secret-like key at {path}.{key}")
            if UNSUPPORTED_KEY.search(str(key)):
                _error(
                    errors, "unsupported_quantification", f"unsupported metric key at {path}.{key}"
                )
            _walk(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, errors, f"{path}[{index}]")


def _required_mapping(
    value: Any, keys: set[str], errors: list[ValidationError], code: str, path: str
) -> None:
    if not isinstance(value, dict) or not keys.issubset(value):
        _error(
            errors,
            code,
            f"{path} is missing required fields: {sorted(keys - set(value) if isinstance(value, dict) else keys)}",
        )


def _validate_bindings(
    outcome: Mapping[str, Any], expected_task_id: str | None, errors: list[ValidationError]
) -> None:
    task_id = outcome.get("workItemId")
    if (
        not isinstance(task_id, str)
        or not TASK_ID.fullmatch(task_id)
        or (expected_task_id and task_id != expected_task_id)
    ):
        _error(errors, "task_binding", "workItemId does not match the expected Task ID")
    bindings = outcome.get("bindings")
    required = {
        "taskId",
        "contractDigest",
        "summaryDigest",
        "verificationDigest",
        "baseCommit",
        "headCommit",
        "lifecycleStage",
        "pullRequest",
        "aiCockpitVersion",
        "generatorVersion",
    }
    _required_mapping(bindings, required, errors, "binding", "bindings")
    if not isinstance(bindings, dict):
        return
    if bindings.get("taskId") != task_id:
        _error(errors, "binding", "bindings.taskId does not match workItemId")
    for key in ("contractDigest", "summaryDigest", "verificationDigest"):
        if not isinstance(bindings.get(key), str) or not SHA256.fullmatch(bindings[key]):
            _error(errors, "binding", f"{key} is not a SHA-256 digest")
    for key in ("baseCommit", "headCommit"):
        if not isinstance(bindings.get(key), str) or not COMMIT.fullmatch(bindings[key]):
            _error(errors, "binding", f"{key} is not a commit object ID")
    stage = bindings.get("lifecycleStage")
    pull = bindings.get("pullRequest")
    if stage == "pre_merge":
        if pull != {"state": "not_created"}:
            _error(errors, "provenance", "pre_merge pullRequest binding must be not_created")
    elif stage == "post_pr":
        if (
            not isinstance(pull, dict)
            or not isinstance(pull.get("number"), int)
            or pull.get("number", 0) < 1
            or not isinstance(pull.get("url"), str)
            or not pull["url"].startswith("https://")
        ):
            _error(errors, "provenance", "post_pr pullRequest binding is invalid")
    else:
        _error(errors, "provenance", "lifecycleStage is invalid")


def _validate_sections(sections: Any, errors: list[ValidationError]) -> None:
    if not isinstance(sections, dict) or (
        set(sections) != SECTIONS and set(sections) != LEGACY_SECTIONS
    ):
        _error(errors, "section_shape", "sections must contain the supported Outcome section set")
        return
    for key in sections:
        if key not in {"outcomeSummary", "taskOverview"} and not isinstance(sections[key], list):
            _error(errors, "section_shape", f"sections.{key} must be an array")
    if isinstance(sections.get("warnings"), list) and any(
        not isinstance(item, str) for item in sections["warnings"]
    ):
        _error(errors, "section_shape", "sections.warnings items must be text")
    for key in ("outcomeSummary", "taskOverview"):
        if not isinstance(sections[key], str) or not sections[key].strip():
            _error(errors, "section_shape", f"sections.{key} must be non-empty text")


def _validate_events(events: Sequence[Mapping[str, Any]], errors: list[ValidationError]) -> None:
    ids: set[Any] = set()
    for event in events:
        if not isinstance(event, Mapping):
            _error(errors, "event_relationship", "event must be an object")
            continue
        event_id = event.get("eventId")
        if event_id in ids:
            _error(errors, "event_identity", f"duplicate eventId: {event_id}")
        ids.add(event_id)
        for relation in ("correctsEventId", "supersedesEventId"):
            if relation in event and event[relation] not in ids:
                _error(errors, "event_relationship", f"{relation} references missing event")


def _validate_severities(sections: Mapping[str, Any], errors: list[ValidationError]) -> None:
    for section in ("findings", "risks", "residualRisks"):
        values = sections.get(section, [])
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values):
            if isinstance(item, Mapping) and item.get("severity") not in SEVERITIES:
                _error(errors, "severity", f"{section}[{index}].severity is invalid")


def _validate_claims(sections: Mapping[str, Any], errors: list[ValidationError]) -> None:
    warnings = sections.get("warnings", [])
    limitations = sections.get("limitations", [])
    non_risks = sections.get("nonRiskExplanations", [])
    residual = sections.get("residualRisks", [])
    forbidden_claims = sections.get("forbiddenClaims", [])
    limitation_sources = {
        item.get("sourceWarning") for item in limitations if isinstance(item, Mapping)
    }
    non_risk_sources = {
        item.get("sourceWarning") for item in non_risks if isinstance(item, Mapping)
    }
    residual_sources = {item.get("sourceWarning") for item in residual if isinstance(item, Mapping)}
    for warning in (item for item in warnings if isinstance(item, str)):
        if warning not in limitation_sources or not (
            warning in non_risk_sources or warning in residual_sources
        ):
            _error(
                errors,
                "warning_binding",
                "warnings require structured limitation and residual-risk or non-risk bindings",
            )
    not_run_warnings = [
        warning for warning in warnings if isinstance(warning, str) and NOT_RUN.search(warning)
    ]
    if not_run_warnings:
        rendered_text = " ".join(
            str(sections.get(key, ""))
            for key in ("outcomeSummary", "taskOverview", "deliveredChanges", "findings")
        )
        if INCOMPATIBLE_VERIFIED_CLAIM.search(rendered_text):
            _error(
                errors,
                "not_run_claim",
                "not_run evidence is incompatible with enterprise-ready or platform-verified claims",
            )
    if sections.get("warnings") and not forbidden_claims:
        _error(errors, "forbidden_claim", "warnings require explicit forbidden claims")
    if sections.get("warnings") and any(
        not isinstance(item, str) or not item.strip() for item in forbidden_claims
    ):
        _error(errors, "forbidden_claim", "forbidden claims must be non-empty text")
    if sections.get("warnings") and not all(
        isinstance(item, Mapping) and isinstance(item.get("sourceWarning"), str)
        for item in limitations
    ):
        _error(errors, "warning_binding", "limitations must identify their source warning")
    for risk in residual:
        if not isinstance(risk, Mapping) or risk.get("severity") not in {"high", "critical"}:
            continue
        for key in ("decisionOwner", "requiredEvidence", "mitigation", "acceptanceStatus"):
            if not risk.get(key):
                _error(errors, "residual_risk", f"high residual risk requires {key}")
    for claim in sections.get("avoidedImpact", []):
        if not isinstance(claim, str) or not claim.strip().lower().startswith(CONDITIONAL):
            _error(errors, "conditional_claim", "Avoided Impact must use conditional language")
    rendered_text = " ".join(
        str(sections.get(key, ""))
        for key in (
            "outcomeSummary",
            "taskOverview",
            "deliveredChanges",
            "warnings",
            "humanDecisions",
        )
    )
    if (
        re.search(r"\bscore\s*[:=]", rendered_text, re.IGNORECASE)
        or re.search(r"\b\d+(?:\.\d+)?\s*%", rendered_text)
        or re.search(r"\b\d+(?:\.\d+)?\s*(?:hours?|percent|money)\b", rendered_text, re.IGNORECASE)
    ):
        _error(
            errors, "unsupported_quantification", "unsupported quantitative claim in report text"
        )
    risks = sections.get("risks", [])
    residual_keys = {
        (item.get("title"), item.get("state")) for item in residual if isinstance(item, Mapping)
    }
    for risk in risks:
        if (
            isinstance(risk, Mapping)
            and risk.get("state") in {"accepted", "unresolved"}
            and (risk.get("title"), risk.get("state")) not in residual_keys
        ):
            _error(errors, "residual_risk", f"residual risk is hidden: {risk.get('title')}")


def _validate_markdown(
    markdown: str | None, sections: Mapping[str, Any], errors: list[ValidationError]
) -> None:
    if markdown is None:
        return
    titles = (
        "Findings",
        "Risks",
        "Warnings",
        "Limitations",
        "Non-Risk Explanations",
        "Forbidden Claims",
        "Interventions",
        "Forced Stops",
        "Resolutions",
        "Recurrence Prevention",
        "Avoided Impact",
        "Residual Risks",
        "Human Decisions",
        "Evidence",
    )
    if any(f"## {title}" not in markdown for title in titles):
        _error(errors, "markdown_parity", "Markdown is missing a required section")
    for key, title in (("findings", "Findings"), ("residualRisks", "Residual Risks")):
        if not sections[key] and f"## {title}\nNone" not in markdown:
            _error(errors, "markdown_parity", f"empty {title} section must say None")


def validate_outcome(
    outcome: Any,
    markdown: str | None = None,
    *,
    events: Sequence[Mapping[str, Any]] = (),
    expected_task_id: str | None = None,
) -> ValidationReport:
    """Validate one Outcome and return structured errors without mutating input."""

    errors: list[ValidationError] = []
    if not isinstance(outcome, dict):
        return ValidationReport(False, (ValidationError("schema", "outcome must be an object"),))
    required = {"format", "schemaVersion", "workItemId", "status", "bindings", "sections"}
    _required_mapping(outcome, required, errors, "schema", "outcome")
    if outcome.get("format") != "ai-cockpit-task-outcome" or outcome.get("schemaVersion") != 1:
        _error(errors, "schema", "format or schemaVersion is invalid")
    if outcome.get("status") not in STATUSES:
        _error(errors, "schema", "status is invalid")
    _validate_bindings(outcome, expected_task_id, errors)
    _validate_sections(outcome.get("sections"), errors)
    if isinstance(outcome.get("sections"), dict):
        _validate_claims(outcome["sections"], errors)
        _validate_severities(outcome["sections"], errors)
        _validate_markdown(markdown, outcome["sections"], errors)
    _validate_events(events, errors)
    _walk(outcome, errors)
    return ValidationReport(not errors, tuple(errors))
