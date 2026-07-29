"""Render a Task Outcome JSON object as a deterministic Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SECTION_TITLES = (
    ("outcomeSummary", "Outcome Summary"),
    ("taskOverview", "Task Overview"),
    ("deliveredChanges", "Delivered Changes"),
    ("findings", "Findings"),
    ("risks", "Risks"),
    ("warnings", "Warnings"),
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


def _item_lines(item: Any) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"- {_item_text(item)}"]
    lines = [f"- {_item_text(item)}"]
    facts = []
    for label, key in (("Category", "category"), ("Severity", "severity"), ("State", "state")):
        value = item.get(key)
        if isinstance(value, str) and value:
            facts.append(f"{label}: {value}")
    if facts:
        lines.append(f"  {'; '.join(facts)}")
    for key in ("description", "reason", "action", "verification", "result", "coverage", "limits"):
        value = item.get(key)
        if isinstance(value, str) and value:
            lines.append(f"  {value}")
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        for ref in evidence:
            if not isinstance(ref, Mapping):
                continue
            source = ref.get("source")
            subject = ref.get("subject")
            if isinstance(source, str) and isinstance(subject, str) and source and subject:
                lines.append(f"  Evidence: {source} — {subject}")
    return lines


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
            for item in value:
                lines.extend(_item_lines(item))
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
