import hashlib
import json
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


def test_current_report_is_aligned_and_generated_files_match():
    report = build_report()
    assert report["status"] == "aligned"
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
    monkeypatch.setattr(docs_metadata, "build_report", lambda root: {"blockingFindings": []})
    monkeypatch.setattr(
        docs_metadata,
        "generated_artifact_errors",
        lambda root, report: ["generated report is stale"],
    )

    assert docs_metadata.main() == 1
    assert (
        "pre-release documentation alignment: generated report is stale" in capsys.readouterr().err
    )


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


@pytest.mark.parametrize("value", ["../outside.md", "/absolute.md", "."])
def test_normalized_path_rejects_escape(value):
    with pytest.raises(AlignmentError):
        normalized_path(value)
