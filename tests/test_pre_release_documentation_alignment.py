import hashlib
import json
from pathlib import Path

import pytest

from check_pre_release_documentation_alignment import (
    AlignmentError,
    bound_evidence_errors,
    build_report,
    digest,
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
