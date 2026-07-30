from __future__ import annotations

import json
from pathlib import Path

import pytest
from ai_quality_architecture import build_report, inspect_source

ROOT = Path(__file__).resolve().parents[1]


def test_repository_quality_architecture_has_no_observed_unsafe_patterns() -> None:
    report = build_report(ROOT)
    assert report["status"] == "pass"
    assert report["safetyFindings"] == []


def test_test_layer_report_is_explicit_and_nonempty() -> None:
    report = build_report(ROOT)
    assert set(report["testLayers"]) >= {"unit", "security_regression", "release", "documentation"}
    assert all(
        item["status"] in {"verified", "not_applicable"} for item in report["testLayers"].values()
    )
    assert all("evidence" in item and "reason" in item for item in report["testLayers"].values())


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ("import subprocess\nsubprocess.run(command, shell=True)\n", "shell_true"),
        ("value = '../secrets'\n", "path_traversal_literal"),
        ("def f(value=[]):\n    return value\n", "mutable_default"),
    ],
)
def test_unsafe_patterns_fail_closed(tmp_path: Path, source: str, kind: str) -> None:
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    assert any(item["kind"] == kind for item in inspect_source(path))


def test_symlink_inputs_fail_closed(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("value = 1\n", encoding="utf-8")
    link = tmp_path / "link.py"
    link.symlink_to(target)
    assert inspect_source(link)[0]["kind"] == "symlink_input"


def test_non_utf8_inputs_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "invalid.py"
    path.write_bytes(b"value = '\xff'\n")
    assert inspect_source(path)[0]["kind"] == "encoding_error"


def test_output_is_json_serializable() -> None:
    report = build_report(ROOT)
    assert json.loads(json.dumps(report, ensure_ascii=False))["schemaVersion"] == 1
