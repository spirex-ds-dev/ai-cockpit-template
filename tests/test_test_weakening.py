"""Behavior tests for the evidence-backed Test Weakening Guard."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import ai_check_test_weakening as checker

ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _repository(tmp_path: Path, files: dict[str, str]) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "baseline")
    return repo, _git(repo, "rev-parse", "HEAD")


def _run(
    repo: Path,
    base: str,
    *,
    mode: str = "full",
    request: str = "",
    policy: Path | None = None,
):
    command = [
        "--root",
        str(repo),
        "--base-ref",
        base,
        "--mode",
        mode,
        "--request",
        request,
    ]
    if policy is not None:
        command.extend(["--policy", str(policy)])
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        returncode = checker.main(command)
    return subprocess.CompletedProcess(
        command, returncode, stdout=stdout.getvalue(), stderr=stderr.getvalue()
    )


def _write(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_material_assertion_reduction_and_skip_require_review(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_order.py": """def test_total():
    assert total(1) == 1
    assert total(2) == 2
    assert total(3) == 3
    assert total(4) == 4
    assert total(5) == 5
    assert total(6) == 6
    assert total(7) == 7
    assert total(8) == 8
"""
        },
    )
    (repo / "tests/test_order.py").write_text(
        """import pytest

@pytest.mark.skip(reason="temporarily disabled")
def test_total():
    assert total(1) == 1
    assert total(2) == 2
""",
        encoding="utf-8",
    )

    result = _run(repo, base)

    assert result.stderr == ""
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["version"] == 1
    assert report["decision"] == "review"
    assert {signal["type"] for signal in report["signals"]} >= {
        "assertion_reduction",
        "skip_added",
    }
    assert report["requiredExplanation"] is True
    assert report["recoveryCondition"]


def test_new_test_file_with_skip_does_not_weaken_existing_tests(tmp_path: Path) -> None:
    repo, base = _repository(tmp_path, {"README.md": "baseline\n"})
    _write(
        repo,
        "tests/test_future.py",
        """import pytest

@pytest.mark.skip(reason="not supported yet")
def test_future():
    assert future_feature()
""",
    )
    _git(repo, "add", "tests/test_future.py")

    result = _run(repo, base)

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["decision"] == "continue"
    assert report["signals"] == []


def test_explicit_request_to_delete_failing_tests_is_blocked(tmp_path: Path) -> None:
    repo, base = _repository(tmp_path, {"README.md": "baseline\n"})

    result = _run(repo, base, request="Delete the failing tests so CI passes.")

    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["decision"] == "block"
    assert [signal["type"] for signal in report["signals"]] == ["explicit_test_bypass_request"]


def test_security_or_regression_test_deletion_is_blocked(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_security_regression.py": """def test_rejects_traversal_regression():
    with pytest.raises(ValueError):
        parse('../secret')
"""
        },
    )
    (repo / "tests/test_security_regression.py").unlink()

    result = _run(repo, base)

    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["decision"] == "block"
    assert {signal["type"] for signal in report["signals"]} >= {
        "test_file_deleted",
        "security_test_deleted",
        "regression_test_deleted",
    }


def test_removed_case_and_exception_assertion_require_review(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_parser.py": """def test_valid():
    assert parse('ok')

def test_invalid():
    with pytest.raises(ValueError):
        parse('bad')
"""
        },
    )
    _write(
        repo,
        "tests/test_parser.py",
        """def test_valid():
    assert parse('ok')
""",
    )

    result = _run(repo, base)

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert {signal["type"] for signal in report["signals"]} >= {
        "test_case_removed",
        "exception_assertion_removed",
        "negative_test_removed",
    }


def test_ci_success_bypasses_are_blocked(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            ".github/workflows/ci.yml": """jobs:
  test:
    steps:
      - run: pytest tests
"""
        },
    )
    _write(
        repo,
        ".github/workflows/ci.yml",
        """jobs:
  test:
    continue-on-error: true
    steps:
      - run: pytest tests || true
""",
    )

    result = _run(repo, base)

    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert {signal["type"] for signal in report["signals"]} >= {
        "ci_continue_on_error_added",
        "test_command_success_bypass_added",
    }


def test_coverage_scope_weakening_requires_review(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            ".coveragerc": """[run]
source = src,lib

[report]
fail_under = 90
omit = tests/*
"""
        },
    )
    _write(
        repo,
        ".coveragerc",
        """[run]
source = src

[report]
fail_under = 80
omit = tests/*,src/legacy/*
""",
    )

    result = _run(repo, base)

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert {signal["type"] for signal in report["signals"]} >= {
        "coverage_exclusion_added",
        "coverage_source_reduced",
        "coverage_threshold_lowered",
    }


def test_lowering_coverage_to_make_current_result_pass_is_blocked(tmp_path: Path) -> None:
    repo, base = _repository(tmp_path, {".coveragerc": "[report]\nfail_under = 90\n"})
    _write(repo, ".coveragerc", "[report]\nfail_under = 70\n")

    result = _run(repo, base, request="Lower coverage to 70 so the current result passes.")

    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["decision"] == "block"
    assert "coverage_threshold_lowered_to_pass" in {signal["type"] for signal in report["signals"]}


def test_removed_test_command_scope_requires_review(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {"Makefile": "test:\n\tpytest tests/unit tests/integration\n"},
    )
    _write(repo, "Makefile", "test:\n\tpytest tests/unit\n")

    result = _run(repo, base)

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert "test_command_scope_reduced" in {signal["type"] for signal in report["signals"]}


def test_small_snapshot_change_is_warning_but_large_churn_is_review(
    tmp_path: Path,
) -> None:
    before = "\n".join(f"line {index}" for index in range(30)) + "\n"
    repo, base = _repository(tmp_path, {"tests/snapshots/view.snap": before})
    _write(repo, "tests/snapshots/view.snap", before.replace("line 1", "line one", 1))

    small = _run(repo, base)

    assert small.returncode == 0
    small_report = json.loads(small.stdout)
    assert small_report["decision"] == "warning"
    assert small_report["signals"][0]["type"] == "snapshot_changed"

    _write(
        repo,
        "tests/snapshots/view.snap",
        "\n".join(f"replacement {index}" for index in range(30)) + "\n",
    )
    large = _run(repo, base)

    assert large.returncode == 2
    assert json.loads(large.stdout)["signals"][0]["type"] == "snapshot_churn"


def test_fast_mode_skips_expensive_semantic_counts_but_keeps_obvious_bypass(
    tmp_path: Path,
) -> None:
    repo, base = _repository(
        tmp_path,
        {"tests/test_fast.py": "def test_value():\n    assert value()\n    assert other()\n"},
    )
    _write(repo, "tests/test_fast.py", "def test_value():\n    assert value()\n")

    result = _run(repo, base, mode="fast")

    assert result.returncode == 0
    assert json.loads(result.stdout)["signals"] == []


def test_invalid_base_and_symlink_escape_fail_closed(tmp_path: Path) -> None:
    repo, base = _repository(tmp_path, {"tests/test_safe.py": "def test_safe():\n    assert 1\n"})
    invalid = _run(repo, "not-a-revision")
    assert invalid.returncode == 4
    assert "invalid Git base" in invalid.stderr

    outside = tmp_path / "outside.py"
    outside.write_text("def test_outside():\n    assert 1\n", encoding="utf-8")
    (repo / "tests/test_safe.py").unlink()
    (repo / "tests/test_safe.py").symlink_to(outside)
    escaped = _run(repo, base)

    assert escaped.returncode == 4
    assert "escapes repository" in escaped.stderr


def test_test_rename_is_warning_not_deletion(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path, {"tests/test_old_name.py": "def test_value():\n    assert value()\n"}
    )
    _git(repo, "mv", "tests/test_old_name.py", "tests/test_new_name.py")

    result = _run(repo, base)

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["decision"] == "warning"
    assert [signal["type"] for signal in report["signals"]] == ["test_renamed"]


def test_case_rename_with_preserved_strength_is_warning(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_math.py": """def test_add():
    assert add(1, 2) == 3
"""
        },
    )
    _write(
        repo,
        "tests/test_math.py",
        """def test_math():
    assert add(1, 2) == 3
    assert subtract(3, 2) == 1
""",
    )

    result = _run(repo, base)

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["decision"] == "warning"
    assert [signal["type"] for signal in report["signals"]] == ["test_case_renamed_or_refactored"]


def test_minor_assertion_reduction_and_relaxed_condition_warn(tmp_path: Path) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_response.py": """def test_response():
    assert response.status == 403
    assert response.body == 'denied'
    assert response.headers['secure'] == 'true'
"""
        },
    )
    _write(
        repo,
        "tests/test_response.py",
        """def test_response():
    assert response.status
    assert response.body == 'denied'
""",
    )

    result = _run(repo, base)

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["decision"] == "warning"
    assert {signal["type"] for signal in report["signals"]} >= {
        "assertion_reduction",
        "assertion_condition_relaxed",
    }


def test_required_check_made_nonblocking_requires_review(tmp_path: Path) -> None:
    repo, base = _repository(tmp_path, {".github/workflows/ci.yml": "checks:\n  required: true\n"})
    _write(repo, ".github/workflows/ci.yml", "checks:\n  required: false\n")

    result = _run(repo, base)

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["signals"][0]["type"] == "required_check_made_nonblocking"


def test_policy_thresholds_are_applied_and_malformed_policy_fails_closed(
    tmp_path: Path,
) -> None:
    repo, base = _repository(
        tmp_path,
        {
            "tests/test_policy.py": """def test_policy():
    assert first()
    assert second()
    assert third()
"""
        },
    )
    _write(repo, "tests/test_policy.py", "def test_policy():\n    assert first()\n")
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        "version: 1\nthresholds:\n  materialAssertionMinimumBefore: 3\n  materialAssertionRatio: 0.5\n  snapshotReviewChangedLines: 12\n",
        encoding="utf-8",
    )

    configured = _run(repo, base, policy=policy)

    assert configured.returncode == 2
    assert json.loads(configured.stdout)["signals"][0]["severity"] == "high"

    policy.write_text("version: nope\nthresholds: []\n", encoding="utf-8")
    malformed = _run(repo, base, policy=policy)
    assert malformed.returncode == 4
    assert "invalid test weakening policy" in malformed.stderr


def test_legacy_report_is_normalized_without_claiming_new_evidence() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from ai_check_test_weakening import normalize_report
    finally:
        sys.path.pop(0)

    report = normalize_report({"decision": "review", "signals": [], "requiredExplanation": True})

    assert report["version"] == 1
    assert report["legacySourceVersion"] == 0
    assert report["decision"] == "review"
    assert report["recoveryCondition"] == "Legacy report requires renewed analysis."


def test_report_schema_accepts_real_output_and_rejects_missing_decision(
    tmp_path: Path,
) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from ai_trust_schema import ValidationError, validate
    finally:
        sys.path.pop(0)

    schema = json.loads(
        (ROOT / ".ai/schemas/test_weakening.schema.json").read_text(encoding="utf-8")
    )
    repo, base = _repository(tmp_path, {"README.md": "baseline\n"})
    report = json.loads(_run(repo, base).stdout)

    validate(report, schema)
    report.pop("decision")
    try:
        validate(report, schema)
    except ValidationError as exc:
        assert "decision" in str(exc)
    else:
        raise AssertionError("schema accepted a report without a decision")


def test_make_entrypoints_execute_the_checker_in_template_and_adopter(
    tmp_path: Path,
) -> None:
    repo, base = _repository(tmp_path, {"README.md": "baseline\n"})
    _write(repo, "README.md", "baseline\nchanged\n")
    (repo / "scripts").mkdir()
    (repo / ".ai/guards").mkdir(parents=True)
    for name in ("ai_check_test_weakening.py", "ai_common.py"):
        shutil.copy2(ROOT / "scripts" / name, repo / "scripts" / name)
    shutil.copy2(
        ROOT / ".ai/guards/test_weakening_policy.yaml",
        repo / ".ai/guards/test_weakening_policy.yaml",
    )

    for makefile in (ROOT / "Makefile", ROOT / "templates/make/Makefile.ai"):
        result = subprocess.run(
            [
                "make",
                "-f",
                str(makefile),
                "check-ai-test-weakening",
                f"AI_BASE_COMMIT={base}",
                f"PYTHON={sys.executable}",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        assert '"decision": "continue"' in result.stdout
