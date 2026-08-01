"""Render a Task Outcome JSON object as a deterministic Markdown report."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SECTION_TITLES = (
    ("outcomeSummary", "Outcome Summary"),
    ("taskOverview", "Task Overview"),
    ("deliveredChanges", "Delivered Changes"),
    ("findings", "Findings"),
    ("risks", "Risks"),
    ("warnings", "Warnings"),
    ("limitations", "Limitations"),
    ("nonRiskExplanations", "Non-Risk Explanations"),
    ("forbiddenClaims", "Forbidden Claims"),
    ("interventions", "Interventions"),
    ("forcedStops", "Forced Stops"),
    ("resolutions", "Resolutions"),
    ("recurrencePrevention", "Recurrence Prevention"),
    ("avoidedImpact", "Avoided Impact"),
    ("residualRisks", "Residual Risks"),
    ("humanDecisions", "Human Decisions"),
    ("evidence", "Evidence"),
)


def _item_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, Mapping):
        for key in ("title", "subject", "problem", "kind", "stage", "source"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(dict(item), ensure_ascii=False, sort_keys=True)
    return str(item)


def render_task_outcome(outcome: Mapping[str, Any]) -> str:
    """Render all machine sections without modifying the input mapping."""

    task_id = outcome.get("workItemId", "unknown-task")
    status = outcome.get("status", "unknown")
    sections = outcome.get("sections", {})
    lines = [f"# Task Outcome: {task_id}", "", f"Status: `{status}`", ""]
    for key, title in SECTION_TITLES:
        lines.append(f"## {title}")
        value = sections.get(key, []) if isinstance(sections, Mapping) else []
        if key in {"outcomeSummary", "taskOverview"}:
            lines.append(value if isinstance(value, str) and value else "None")
        elif isinstance(value, list) and value:
            lines.extend(f"- {_item_text(item)}" for item in value)
        else:
            lines.append("None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    outcome = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(render_task_outcome(outcome), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
