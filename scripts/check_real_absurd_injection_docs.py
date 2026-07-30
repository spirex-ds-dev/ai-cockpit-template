"""Check the complete, aligned multilingual real-case assessment records."""

from __future__ import annotations

import re
from pathlib import Path


CASE_IDS = tuple(f"RAI-{number:02d}" for number in range(1, 13))
DOCUMENTS = (
    "docs/reference/real-absurd-injection-cases.md",
    "docs/reference/real-absurd-injection-cases.zh-CN.md",
    "docs/reference/real-absurd-injection-cases.ja.md",
)
_RECORD = re.compile(
    r"<!-- real-case: (RAI-\d{2}) \| status: ([a-z_]+) \| "
    r"decision: ([a-z_]+) \| gate: ([a-z_]+) -->"
)
_FULL_RECORD = re.compile(r"<!-- full-case: (RAI-\d{2}) \| result: ([a-z_]+) -->")
FULL_RESULTS = (
    "not_proven",
    "block",
    "block",
    "block",
    "review",
    "block",
    "block",
    "block",
    "block",
    "block",
    "block",
    "block",
)


def _records(path: Path) -> list[tuple[str, str, str, str]]:
    return [tuple(match.groups()) for match in _RECORD.finditer(path.read_text(encoding="utf-8"))]


def _full_records(path: Path) -> list[tuple[str, str]]:
    return [
        tuple(match.groups()) for match in _FULL_RECORD.finditer(path.read_text(encoding="utf-8"))
    ]


def check_repository(root: Path) -> list[str]:
    """Return actionable errors; keep language content and outcome metadata aligned."""

    errors: list[str] = []
    baseline: list[tuple[str, str, str, str]] | None = None
    for relative_path in DOCUMENTS:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing assessment document: {relative_path}")
            continue
        records = _records(path)
        ids = tuple(record[0] for record in records)
        if ids != CASE_IDS:
            errors.append(f"{relative_path}: expected one ordered record for every case ID")
        if baseline is None:
            baseline = records
        elif records != baseline:
            errors.append(f"{relative_path}: case status, decision, or gate differs from English")
        if "not_covered" not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative_path}: must state current evidence gaps")
        full_records = _full_records(path)
        if tuple(case_id for case_id, _result in full_records) != CASE_IDS:
            errors.append(
                f"{relative_path}: expected one ordered full-repository record for every case ID"
            )
        elif tuple(result for _case_id, result in full_records) != FULL_RESULTS:
            errors.append(
                f"{relative_path}: full-repository results differ from the verified assessment"
            )
    return errors


if __name__ == "__main__":
    problems = check_repository(Path(__file__).resolve().parents[1])
    if problems:
        raise SystemExit("\n".join(problems))
