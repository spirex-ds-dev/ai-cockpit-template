#!/usr/bin/env python3
"""Query evidence-bound Implementation Knowledge records deterministically."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ai_check_knowledge_index import check_index

KNOWLEDGE_STATES = {"verified", "partial", "unknown", "superseded"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class KnowledgeQueryError(ValueError):
    """Raised when the authoritative knowledge input cannot be queried safely."""


@dataclass(frozen=True)
class QueryFilters:
    """Exact structured filters supported by the query interface."""

    work_item_id: str | None = None
    topic: str | None = None
    component: str | None = None
    commit: str | None = None
    date_exact: str | None = None
    status: str | None = None
    date_from: str | None = None
    date_to: str | None = None

    def validate(self) -> None:
        if self.status is not None and self.status not in KNOWLEDGE_STATES:
            allowed = ", ".join(sorted(KNOWLEDGE_STATES))
            raise KnowledgeQueryError(f"status must be one of: {allowed}")
        if self.commit is not None and not re.fullmatch(r"[0-9a-f]{40}", self.commit):
            raise KnowledgeQueryError("commit must be a 40-character lowercase hexadecimal SHA")
        for field, value in (
            ("date", self.date_exact),
            ("date-from", self.date_from),
            ("date-to", self.date_to),
        ):
            if value is not None:
                _parse_date(value, field)
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise KnowledgeQueryError("date-from must not be later than date-to")


def _parse_date(value: str, label: str) -> date:
    if not DATE_PATTERN.fullmatch(value):
        raise KnowledgeQueryError(f"{label} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise KnowledgeQueryError(f"{label} is not a calendar date") from exc


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeQueryError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise KnowledgeQueryError(f"{path} must contain a JSON object")
    return value


def _safe_repo_path(path_text: str, *, repo_root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts or "" in path.parts:
        raise KnowledgeQueryError(f"knowledge path is not repository-relative: {path_text}")
    candidate = (repo_root / path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise KnowledgeQueryError(f"knowledge path escapes repository: {path_text}") from exc
    return candidate


def _record_date(record: dict[str, Any]) -> str | None:
    value = record.get("date")
    return value if isinstance(value, str) and value else None


def _matches(record: dict[str, Any], filters: QueryFilters) -> bool:
    if filters.work_item_id is not None and record.get("workItemId") != filters.work_item_id:
        return False
    if filters.topic is not None and filters.topic not in record.get("topics", []):
        return False
    if filters.component is not None and filters.component not in record.get("components", []):
        return False
    if filters.commit is not None and record.get("mergedCommit") != filters.commit:
        return False
    if filters.status is not None and record.get("knowledgeState") != filters.status:
        return False

    requested_dates = any(
        value is not None for value in (filters.date_exact, filters.date_from, filters.date_to)
    )
    if not requested_dates:
        return True
    value = _record_date(record)
    if value is None:
        return False
    candidate = _parse_date(value, "record date")
    if filters.date_exact is not None and value != filters.date_exact:
        return False
    if filters.date_from is not None and candidate < _parse_date(filters.date_from, "date-from"):
        return False
    return not (filters.date_to is not None and candidate > _parse_date(filters.date_to, "date-to"))


def _validate_authoritative_inputs(*, index_path: Path, records_dir: Path, repo_root: Path) -> None:
    issues = check_index(index_path, records_dir=records_dir, repo_root=repo_root)
    if issues:
        raise KnowledgeQueryError("knowledge index is invalid: " + "; ".join(issues))


def query_knowledge(
    *,
    repo_root: Path,
    index_path: Path,
    records_dir: Path,
    filters: QueryFilters,
) -> dict[str, Any]:
    """Return a stable, read-only query result over validated knowledge records."""
    filters.validate()
    repo_root = repo_root.resolve()
    index_path = index_path.resolve()
    records_dir = records_dir.resolve()
    _validate_authoritative_inputs(
        index_path=index_path, records_dir=records_dir, repo_root=repo_root
    )
    index = _load_object(index_path)
    entries = index.get("workItems")
    if not isinstance(entries, list):
        raise KnowledgeQueryError("knowledge index workItems must be an array")

    matches: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise KnowledgeQueryError("knowledge index contains a non-object entry")
        knowledge_path = entry.get("knowledgePath")
        if not isinstance(knowledge_path, str) or not knowledge_path:
            raise KnowledgeQueryError("knowledge index entry has no knowledgePath")
        record_path = _safe_repo_path(knowledge_path, repo_root=repo_root)
        if not record_path.is_file():
            raise KnowledgeQueryError(f"missing record: {knowledge_path}")
        record = _load_object(record_path)
        if record.get("workItemId") != entry.get("workItemId"):
            raise KnowledgeQueryError(f"record identity mismatch: {knowledge_path}")
        if _matches(record, filters):
            matches.append({"knowledgePath": knowledge_path, "record": record})

    matches.sort(key=lambda item: (item["record"]["workItemId"], item["knowledgePath"]))
    return {
        "schemaVersion": 1,
        "query": asdict(filters),
        "matchedCount": len(matches),
        "matches": matches,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path)
    parser.add_argument("--records-dir", type=Path)
    parser.add_argument("--work-item-id")
    parser.add_argument("--topic")
    parser.add_argument("--component")
    parser.add_argument("--commit")
    parser.add_argument("--date", dest="date_exact")
    parser.add_argument("--status", choices=sorted(KNOWLEDGE_STATES))
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    index_path = args.index or repo_root / ".ai" / "knowledge" / "index.json"
    records_dir = args.records_dir or repo_root / ".ai" / "knowledge" / "work-items"
    filters = QueryFilters(
        work_item_id=args.work_item_id,
        topic=args.topic,
        component=args.component,
        commit=args.commit,
        date_exact=args.date_exact,
        status=args.status,
        date_from=args.date_from,
        date_to=args.date_to,
    )
    try:
        result = query_knowledge(
            repo_root=repo_root,
            index_path=index_path,
            records_dir=records_dir,
            filters=filters,
        )
    except KnowledgeQueryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
