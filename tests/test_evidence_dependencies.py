"""Tests for Capability Truth evidence dependency discovery."""

from __future__ import annotations

import json
import re
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from ai_evidence_dependencies import (
    changed_path_dependency_issues,
    contract_scope_dependency_issues,
    load_capability_evidence_dependencies,
)


MATRIX_PATH = "docs/reference/capability-truth-matrix.json"
MARKDOWN_PATH = "docs/reference/capability-truth-matrix.md"


def write_file(root: Path, relative_path: str, content: str = "evidence\n") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_matrix(root: Path, value: Any) -> None:
    path = root / MATRIX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def capability(
    identifier: str,
    *,
    source: list[Any] | None = None,
    tests: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "sourceEvidence": ["src/source.py"] if source is None else source,
        "testEvidence": ["tests/test_source.py"] if tests is None else tests,
    }


def test_loader_deduplicates_shared_paths_and_sorts_dependency_graph(tmp_path: Path) -> None:
    for path in (
        "src/alpha.py",
        "src/shared.py",
        "src/zeta.py",
        "tests/test_alpha.py",
        "tests/test_zeta.py",
    ):
        write_file(tmp_path, path)
    write_matrix(
        tmp_path,
        {
            "capabilities": [
                capability(
                    "zeta",
                    source=["src/zeta.py", "src/shared.py"],
                    tests=["tests/test_zeta.py"],
                ),
                capability(
                    "alpha",
                    source=["src/shared.py", "src/alpha.py"],
                    tests=["tests/test_alpha.py"],
                ),
            ]
        },
    )

    dependencies = load_capability_evidence_dependencies(tmp_path)

    assert dependencies is not None
    assert dependencies.matrix_path == MATRIX_PATH
    assert list(dependencies.capability_ids_by_path) == [
        "src/alpha.py",
        "src/shared.py",
        "src/zeta.py",
        "tests/test_alpha.py",
        "tests/test_zeta.py",
    ]
    assert dict(dependencies.capability_ids_by_path) == {
        "src/alpha.py": ("alpha",),
        "src/shared.py": ("alpha", "zeta"),
        "src/zeta.py": ("zeta",),
        "tests/test_alpha.py": ("alpha",),
        "tests/test_zeta.py": ("zeta",),
    }
    assert dependencies.source_paths == (
        "src/alpha.py",
        "src/shared.py",
        "src/zeta.py",
    )
    assert dependencies.test_paths == (
        "tests/test_alpha.py",
        "tests/test_zeta.py",
    )
    with pytest.raises(FrozenInstanceError):
        dependencies.source_paths = ()
    with pytest.raises(TypeError):
        dependencies.capability_ids_by_path["src/shared.py"] = ("changed",)


def test_loader_returns_none_only_when_capability_truth_is_not_configured(
    tmp_path: Path,
) -> None:
    assert load_capability_evidence_dependencies(tmp_path) is None


def test_loader_rejects_missing_json_when_markdown_configures_document_set(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, MARKDOWN_PATH)

    with pytest.raises(ValueError, match=re.escape(MATRIX_PATH)):
        load_capability_evidence_dependencies(tmp_path)


@pytest.mark.parametrize(
    ("value", "diagnostic"),
    [
        ([], MATRIX_PATH),
        ({}, "capabilities"),
        ({"capabilities": {}}, "capabilities"),
        ({"capabilities": ["not-an-object"]}, "capabilities[0]"),
        (
            {
                "capabilities": [
                    {
                        "sourceEvidence": ["src/source.py"],
                        "testEvidence": ["tests/test_source.py"],
                    }
                ]
            },
            "capabilities[0].id",
        ),
        (
            {
                "capabilities": [
                    capability("duplicate"),
                    capability("duplicate"),
                ]
            },
            "duplicate",
        ),
        (
            {
                "capabilities": [
                    {
                        "id": "invalid-source-list",
                        "sourceEvidence": "src/source.py",
                        "testEvidence": ["tests/test_source.py"],
                    }
                ]
            },
            "capabilities[0].sourceEvidence",
        ),
        (
            {
                "capabilities": [
                    {
                        "id": "invalid-test-list",
                        "sourceEvidence": ["src/source.py"],
                        "testEvidence": "tests/test_source.py",
                    }
                ]
            },
            "capabilities[0].testEvidence",
        ),
        (
            {
                "capabilities": [
                    capability("non-string-source", source=[7]),
                ]
            },
            "capabilities[0].sourceEvidence[0]",
        ),
        (
            {
                "capabilities": [
                    capability("non-string-test", tests=[False]),
                ]
            },
            "capabilities[0].testEvidence[0]",
        ),
    ],
)
def test_loader_rejects_malformed_manifest_structure(
    tmp_path: Path, value: Any, diagnostic: str
) -> None:
    write_file(tmp_path, "src/source.py")
    write_file(tmp_path, "tests/test_source.py")
    write_matrix(tmp_path, value)

    with pytest.raises(ValueError, match=re.escape(diagnostic)):
        load_capability_evidence_dependencies(tmp_path)


@pytest.mark.parametrize(
    ("raw_path", "setup", "diagnostic"),
    [
        ("/absolute/evidence.py", "none", "/absolute/evidence.py"),
        ("../escaping.py", "none", "../escaping.py"),
        ("missing.py", "none", "missing.py"),
        ("evidence", "directory", "evidence"),
        ("alias.py", "symlink", "alias.py"),
    ],
)
def test_loader_rejects_unsafe_or_non_file_evidence_paths(
    tmp_path: Path, raw_path: str, setup: str, diagnostic: str
) -> None:
    write_file(tmp_path, "tests/test_source.py")
    if setup == "directory":
        (tmp_path / raw_path).mkdir(parents=True)
    elif setup == "symlink":
        write_file(tmp_path, "target.py")
        (tmp_path / raw_path).symlink_to(tmp_path / "target.py")
    write_matrix(
        tmp_path,
        {
            "capabilities": [
                capability("unsafe-path", source=[raw_path]),
            ]
        },
    )

    with pytest.raises(ValueError, match=re.escape(diagnostic)):
        load_capability_evidence_dependencies(tmp_path)


def test_loader_rejects_duplicate_aliases_inside_one_capability(tmp_path: Path) -> None:
    write_file(tmp_path, "src/source.py")
    write_file(tmp_path, "tests/test_source.py")
    write_matrix(
        tmp_path,
        {
            "capabilities": [
                capability(
                    "duplicate-alias",
                    source=["src/source.py", "./src/source.py"],
                )
            ]
        },
    )

    with pytest.raises(ValueError, match=r"duplicate.*\./src/source\.py"):
        load_capability_evidence_dependencies(tmp_path)


def test_loader_rejects_malformed_json_with_matrix_location(tmp_path: Path) -> None:
    matrix_path = tmp_path / MATRIX_PATH
    matrix_path.parent.mkdir(parents=True)
    matrix_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(MATRIX_PATH)):
        load_capability_evidence_dependencies(tmp_path)


def test_contract_scope_dependency_issues_support_exact_and_glob_scope(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, "src/source.py")
    write_file(tmp_path, "tests/test_source.py")
    write_matrix(tmp_path, {"capabilities": [capability("bounded")]})
    dependencies = load_capability_evidence_dependencies(tmp_path)
    assert dependencies is not None

    exact_issues = contract_scope_dependency_issues(["src/source.py"], dependencies)
    glob_issues = contract_scope_dependency_issues(["src/**"], dependencies)

    assert len(exact_issues) == 1
    assert "src/source.py" in exact_issues[0]
    assert "bounded" in exact_issues[0]
    assert MATRIX_PATH in exact_issues[0]
    assert glob_issues == exact_issues
    assert contract_scope_dependency_issues(["src/**", "docs/reference/**"], dependencies) == []
    assert contract_scope_dependency_issues(["docs/unrelated.md"], dependencies) == []
    assert contract_scope_dependency_issues([MATRIX_PATH], dependencies) == []


def test_changed_path_dependency_issues_require_actual_matrix_change(
    tmp_path: Path,
) -> None:
    write_file(tmp_path, "src/source.py")
    write_file(tmp_path, "tests/test_source.py")
    write_matrix(tmp_path, {"capabilities": [capability("bounded")]})
    dependencies = load_capability_evidence_dependencies(tmp_path)
    assert dependencies is not None

    issues = changed_path_dependency_issues(["src/source.py"], dependencies)

    assert len(issues) == 1
    assert "src/source.py" in issues[0]
    assert "bounded" in issues[0]
    assert MATRIX_PATH in issues[0]
    assert changed_path_dependency_issues(["src/source.py", MATRIX_PATH], dependencies) == []
    assert changed_path_dependency_issues(["docs/unrelated.md"], dependencies) == []
    assert changed_path_dependency_issues([MATRIX_PATH], dependencies) == []
