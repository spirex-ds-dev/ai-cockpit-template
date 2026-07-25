"""Render an explicitly approved, sanitized Task Outcome PR fragment.

This module is presentation-only.  It never edits the Outcome JSON and it
never includes machine evidence, provenance, stop details, or unapproved
sections in a pull-request fragment.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from ai_common import parse_yaml


SAFE_FIELDS = (
    "status",
    "outcomeSummary",
    "taskOverview",
    "deliveredChanges",
    "findings",
    "risks",
    "warnings",
    "residualRisks",
)
DEFAULT_FIELDS = ("status", "outcomeSummary")
FIELD_LABELS = {
    "outcomeSummary": "Outcome",
    "taskOverview": "Overview",
    "deliveredChanges": "Delivered Changes",
    "findings": "Findings",
    "risks": "Risks",
    "warnings": "Warnings",
    "residualRisks": "Residual Risks",
}
SECRET = re.compile(
    r"(?i)(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)\s*[:=]\s*[^\s,;]+"
)
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home|private|tmp|var)/[^\s`]+")
UNSUPPORTED_CLAIM = re.compile(
    r"(?i)\b(?:score|productivity|hours? saved|money saved|percent(?:age)?|roi)\b"
)


def _policy(profile: Mapping[str, Any]) -> Mapping[str, Any]:
    reporting = profile.get("reporting", {})
    if not isinstance(reporting, Mapping):
        return {}
    policy = reporting.get("pullRequestSummary", {})
    return policy if isinstance(policy, Mapping) else {}


def _safe_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = SECRET.sub("[redacted]", value.strip())
    text = ABSOLUTE_PATH.sub("[path redacted]", text)
    if UNSUPPORTED_CLAIM.search(text):
        return "[redacted unsupported quantitative claim]"
    return text


def _items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = _safe_text(item)
        elif isinstance(item, Mapping):
            text = ""
            for key in ("title", "subject", "problem", "description", "kind", "stage"):
                text = _safe_text(item.get(key))
                if text:
                    break
        else:
            text = ""
        if text:
            result.append(text)
    return result


def render_pr_summary(outcome: Mapping[str, Any], profile: Mapping[str, Any]) -> str:
    """Return a PR-safe Markdown fragment, or empty string when not approved."""

    policy = _policy(profile)
    if policy.get("enabled") is not True:
        return ""
    requested = policy.get("fields", DEFAULT_FIELDS)
    fields = (
        tuple(field for field in requested if field in SAFE_FIELDS)
        if isinstance(requested, list)
        else DEFAULT_FIELDS
    )
    sections = outcome.get("sections", {})
    if not isinstance(sections, Mapping):
        sections = {}
    lines = ["## Task Outcome Summary", ""]
    for field in fields:
        if field == "status":
            status = _safe_text(outcome.get("status")) or "unknown"
            lines.append(f"- Status: `{status}`")
        elif field == "outcomeSummary":
            lines.append(f"- Outcome: {_safe_text(sections.get(field)) or 'None'}")
        elif field == "taskOverview":
            lines.append(f"- Overview: {_safe_text(sections.get(field)) or 'None'}")
        else:
            values = _items(sections.get(field))
            label = FIELD_LABELS[field]
            if values:
                lines.append(f"- {label}:")
                lines.extend(f"  - {value}" for value in values)
            else:
                lines.append(f"- {label}: None")
    return "\n".join(lines) + "\n"


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outcome", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    outcome = json.loads(args.outcome.read_text(encoding="utf-8"))
    profile = parse_yaml(args.profile) if args.profile.exists() else {}
    rendered = render_pr_summary(outcome, profile)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
