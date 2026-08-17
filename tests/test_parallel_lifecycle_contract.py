"""Regression tests for the guarded parallel Work Item lifecycle contract."""

from __future__ import annotations

import json
from pathlib import Path

import ai_projection_lease as lease
from ai_check_work_item import validate_concurrency_boundary

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PAGES = (
    ROOT / "docs/operations/work-item-lifecycle.md",
    ROOT / "docs/operations/work-item-lifecycle.ja.md",
    ROOT / "docs/operations/work-item-lifecycle.zh-CN.md",
)


def test_canonical_pages_describe_guarded_parallel_work_items() -> None:
    """Break caught: canonical guidance globally serializes otherwise independent work."""
    pages = [path.read_text(encoding="utf-8") for path in CANONICAL_PAGES]

    for page in pages:
        assert "parallel" in page.lower() or "並行" in page or "并行" in page
        assert "one Contract" in page or "一つの Contract" in page or "一个 Contract" in page
        assert "one dedicated branch" in page or "専用 branch" in page or "专用 branch" in page
        assert "one PR" in page or "一つの PR" in page or "一个 PR" in page
        assert "blocked" in page.lower() or "blocked" in page
        assert "Agent" in page or "Agent/Orchestrator" in page
        assert "fail-closed" in page or "fail closed" in page or "fail-closed" in page
        assert "Do not start the next Work Item while the current one is open" not in page
        assert "現在の Work Item を閉じる前に次を始めず" not in page
        assert "当前 Work Item 未关闭前不要开始下一个" not in page


def test_contract_preserves_closed_serialized_projection_boundary() -> None:
    """Break caught: parallel guidance permits ambiguous shared projection ownership."""
    contract = json.loads(
        (
            ROOT / ".ai/work-items/active/canonical-lifecycle-parallel-alignment.contract.json"
        ).read_text(encoding="utf-8")
    )

    assert validate_concurrency_boundary(contract) == []
    assert set(contract["concurrencyBoundary"]["serializedProjectionPaths"]) == set(
        lease.BRANCH_INTEGRATED_GENERATED_PATHS
    )
