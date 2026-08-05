import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import check_docs_metadata as docs_metadata
import check_pre_release_documentation_alignment as alignment
import pytest
from check_pre_release_documentation_alignment import (
    AlignmentError,
    bound_evidence_errors,
    build_report,
    digest,
    generated_artifact_errors,
    marker_errors,
    normalized_path,
    render_markdown,
)


def test_current_report_is_aligned_and_generated_files_match_after_bound_evidence_refresh():
    report = build_report()
    assert report["status"] == "aligned"
    assert report["blockingFindings"] == []
    assert report["digest"] == digest(report)
    assert (
        json.loads(
            Path("docs/reference/pre-release-documentation-alignment.json").read_text(
                encoding="utf-8"
            )
        )
        == report
    )
    assert Path("docs/reference/pre-release-documentation-alignment.md").read_text(
        encoding="utf-8"
    ) == render_markdown(report)


def test_canonical_generator_chain_converges_in_an_isolated_repository(tmp_path):
    source_root = Path(__file__).resolve().parents[1]
    isolated_root = tmp_path / "repository"
    shutil.copytree(
        source_root,
        isolated_root,
        ignore=shutil.ignore_patterns(".git", ".venv", "target", "__pycache__", "*.pyc"),
    )
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    for script in (
        "scripts/ai_capability_truth.py",
        "scripts/ai_japanese_capability.py",
        "scripts/check_pre_release_documentation_alignment.py",
    ):
        result = subprocess.run(
            [sys.executable, script, "--write"],
            cwd=isolated_root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    for script, option in (
        ("scripts/ai_japanese_capability.py", "--check"),
        ("scripts/check_pre_release_documentation_alignment.py", None),
    ):
        command = [sys.executable, script]
        if option is not None:
            command.append(option)
        result = subprocess.run(
            command,
            cwd=isolated_root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_capability_truth_regeneration_cannot_invalidate_japanese_assessment(tmp_path):
    source_root = Path(__file__).resolve().parents[1]
    isolated_root = tmp_path / "repository"
    shutil.copytree(
        source_root,
        isolated_root,
        ignore=shutil.ignore_patterns(".git", ".venv", "target", "__pycache__", "*.pyc"),
    )
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    for script in (
        "scripts/ai_japanese_capability.py",
        "scripts/ai_capability_truth.py",
        "scripts/check_pre_release_documentation_alignment.py",
    ):
        result = subprocess.run(
            [sys.executable, script, "--write"],
            cwd=isolated_root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    result = subprocess.run(
        [sys.executable, "scripts/check_pre_release_documentation_alignment.py"],
        cwd=isolated_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_build_report_blocks_when_injected_bound_evidence_drifts(tmp_path, monkeypatch):
    bound = tmp_path / "bound.md"
    bound.write_text("before", encoding="utf-8")
    checksum = hashlib.sha256(b"before").hexdigest()
    assessment_path = tmp_path / "docs/reference/japanese-capability-assessment.json"
    assessment_path.parent.mkdir(parents=True)
    assessment_path.write_text(
        json.dumps(
            {
                "workItemRole": "final_reassessment",
                "blockingFindings": [],
                "evidenceSource": {"files": [{"path": "bound.md", "sha256": checksum}]},
            }
        ),
        encoding="utf-8",
    )
    surface = tmp_path / "surface.md"
    surface.write_text("required marker", encoding="utf-8")
    plan = tmp_path / "docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("文档对齐 WI-18 WI-19", encoding="utf-8")
    bound.write_text("after", encoding="utf-8")
    monkeypatch.setattr(
        alignment,
        "SURFACES",
        {
            "surface.md": ("test", ("required marker",)),
            "docs/superpowers/plans/2026-07-25-ai-cockpit-comprehensive-remediation.md": (
                "plan",
                ("文档对齐", "WI-18", "WI-19"),
            ),
        },
    )
    monkeypatch.setattr(alignment, "UPDATED_SURFACES", set())
    monkeypatch.setattr(alignment, "check_trust_layer", lambda root: [])

    report = build_report(tmp_path)

    assert report["status"] == "blocked"
    assert report["blockingFindings"] == [
        {
            "findingId": "DOC-ALIGN-001",
            "severity": "blocking",
            "detail": "Japanese bound evidence drift: bound.md",
        }
    ]


def test_generated_artifact_errors_fail_closed_for_stale_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(alignment, "JSON_REPORT", Path("generated.json"))
    monkeypatch.setattr(alignment, "MARKDOWN_REPORT", Path("generated.md"))
    monkeypatch.setattr(alignment, "render_markdown", lambda report: "current markdown\n")
    (tmp_path / "generated.json").write_text('{"old": true}\n', encoding="utf-8")
    (tmp_path / "generated.md").write_text("old markdown\n", encoding="utf-8")

    assert generated_artifact_errors(tmp_path, {"current": True}) == [
        (
            "generated documentation-alignment JSON is stale: generated.json; run "
            "python3 scripts/check_pre_release_documentation_alignment.py --write"
        ),
        (
            "generated documentation-alignment Markdown is stale: generated.md; run "
            "python3 scripts/check_pre_release_documentation_alignment.py --write"
        ),
    ]


def test_metadata_command_includes_pre_release_generated_artifact_gate(monkeypatch, capsys):
    monkeypatch.setattr(docs_metadata, "check_repository", lambda root: [])

    assert docs_metadata.main() == 0
    assert "documentation metadata check passed" in capsys.readouterr().out


def test_marker_matching_handles_wrapped_text_and_missing_marker():
    assert (
        marker_errors(
            "example.md", "Evidence over\nSelf-Declaration", ("Evidence over Self-Declaration",)
        )
        == []
    )
    assert marker_errors("example.md", "different text", ("required marker",)) == [
        "example.md: missing required marker: required marker"
    ]


def test_bound_evidence_fails_closed_for_missing_drift_and_duplicate_paths(tmp_path):
    bound = tmp_path / "bound.md"
    bound.write_text("before", encoding="utf-8")
    checksum = hashlib.sha256(b"before").hexdigest()
    assessment = {"evidenceSource": {"files": [{"path": "bound.md", "sha256": checksum}]}}
    assert bound_evidence_errors(tmp_path, assessment) == []
    bound.write_text("after", encoding="utf-8")
    assert bound_evidence_errors(tmp_path, assessment) == [
        "Japanese bound evidence drift: bound.md"
    ]
    duplicate = {
        "evidenceSource": {
            "files": [
                {"path": "bound.md", "sha256": checksum},
                {"path": "bound.md", "sha256": checksum},
            ]
        }
    }
    assert "Japanese bound path is duplicated: bound.md" in bound_evidence_errors(
        tmp_path, duplicate
    )


def test_japanese_bound_evidence_reports_makefile_capability_and_test_drift(tmp_path):
    paths = [
        "Makefile",
        "docs/reference/capability-truth-matrix.json",
        "tests/test_core_gates.py",
    ]
    rows = []
    for path in paths:
        candidate = tmp_path / path
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("before", encoding="utf-8")
        rows.append({"path": path, "sha256": hashlib.sha256(b"before").hexdigest()})
        candidate.write_text("after", encoding="utf-8")

    assert bound_evidence_errors(tmp_path, {"evidenceSource": {"files": rows}}) == [
        "Japanese bound evidence drift: Makefile",
        "Japanese bound evidence drift: docs/reference/capability-truth-matrix.json",
        "Japanese bound evidence drift: tests/test_core_gates.py",
    ]


@pytest.mark.parametrize("value", ["../outside.md", "/absolute.md", "."])
def test_normalized_path_rejects_escape(value):
    with pytest.raises(AlignmentError):
        normalized_path(value)
