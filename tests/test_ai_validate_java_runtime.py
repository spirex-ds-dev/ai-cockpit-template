"""Regression coverage for the installed Java runtime-major gate."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import ai_validate_java_runtime as validator
import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "ai_validate_java_runtime.py"
JAVA_PRESET = ROOT / "templates" / "stacks" / "java.mk"


def fake_java(tmp_path: Path, version: str) -> Path:
    executable = tmp_path / "java"
    executable.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-version" ]; then\n'
        f"  printf '%s\\n' '{version}' >&2\n"
        "  exit 0\n"
        "fi\n"
        "exit 64\n",
        encoding="utf-8",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def validate(
    *args: str, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_matching_legacy_java_runtime_is_accepted_for_the_declared_lane(tmp_path: Path) -> None:
    java = fake_java(tmp_path, 'java version "1.8.0_412"')

    result = validate(
        "--lane",
        "java8",
        "--required-major",
        "8",
        "--java-command",
        str(java),
    )

    assert result.returncode == 0, result.stderr
    assert "lane 'java8'" in result.stdout
    assert "required major 8" in result.stdout
    assert "actual major 8" in result.stdout


def test_mismatched_runtime_is_blocked_before_a_java_lane_command(tmp_path: Path) -> None:
    java = fake_java(tmp_path, 'openjdk version "21.0.8" 2025-07-15')

    result = validate(
        "--lane",
        "java17",
        "--required-major",
        "17",
        "--java-command",
        str(java),
    )

    assert result.returncode != 0
    assert "BLOCKED" in result.stderr
    assert "lane 'java17' requires Java major 17" in result.stderr
    assert "actual major 21" in result.stderr
    assert "Recovery:" in result.stderr


def test_java_home_selects_the_observed_runtime_for_a_matching_modern_lane(tmp_path: Path) -> None:
    java_home = tmp_path / "jdk-17"
    bin_dir = java_home / "bin"
    bin_dir.mkdir(parents=True)
    selected = fake_java(bin_dir, 'openjdk version "17.0.16" 2025-07-15')
    selected.rename(bin_dir / "java")

    other = fake_java(tmp_path, 'openjdk version "21.0.8" 2025-07-15')
    environment = dict(os.environ, PATH=str(tmp_path))
    result = validate(
        "--lane",
        "java17",
        "--required-major",
        "17",
        "--java-command",
        str(other),
        "--java-home",
        str(java_home),
        environment=environment,
    )

    assert result.returncode == 0, result.stderr
    assert str(bin_dir / "java") in result.stdout


def test_missing_required_major_fails_closed_with_recovery() -> None:
    result = validate("--lane", "java17")

    assert result.returncode != 0
    assert "required Java major is missing" in result.stderr
    assert "Recovery:" in result.stderr


def test_validator_covers_runtime_discovery_branches_in_process(monkeypatch, capsys) -> None:
    """Keep the validator's fail-closed branches inside the measured process."""

    def succeeds(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["java", "-version"],
            returncode=0,
            stdout="",
            stderr='openjdk version "17.0.16" 2025-07-15',
        )

    monkeypatch.setattr(validator.subprocess, "run", succeeds)
    assert validator.main(["--lane", "java17", "--required-major", "17"]) == 0
    assert "actual major 17" in capsys.readouterr().out

    assert validator.main(["--lane", "java17"]) == 2
    assert "required Java major is missing" in capsys.readouterr().err
    assert validator.main(["--lane", "java17", "--required-major", "not-a-major"]) == 2
    assert "is not an integer" in capsys.readouterr().err
    assert validator.main(["--lane", "java17", "--required-major", "0"]) == 2
    assert "is not positive" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("runner", "expected_message"),
    [
        (lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()), "unavailable"),
        (
            lambda *_args, **_kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("java", 15)),
            "timed out",
        ),
        (
            lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", ""),
            "could not query",
        ),
        (
            lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "", "not a version"),
            "version is unreadable",
        ),
        (
            lambda *_args, **_kwargs: subprocess.CompletedProcess(
                [], 0, "", 'openjdk version "21.0.8"'
            ),
            "reports actual major 21",
        ),
    ],
)
def test_validator_fails_closed_for_unusable_or_mismatched_runtime(
    monkeypatch, capsys, runner, expected_message: str
) -> None:
    monkeypatch.setattr(validator.subprocess, "run", runner)

    assert validator.main(["--lane", "java17", "--required-major", "17"]) == 2
    output = capsys.readouterr().err
    assert "BLOCKED:" in output
    assert expected_message in output
    assert "Recovery:" in output


def test_validator_parses_versions_and_java_home_selection_without_subprocess() -> None:
    assert validator.parse_java_major('java version "1.8.0_412"') == 8
    assert validator.parse_java_major('openjdk version "21.0.8"') == 21
    assert validator.parse_java_major("not a Java version") is None
    assert validator.selected_java(java_command="java", java_home="/approved/jdk") == (
        "/approved/jdk/bin/java"
    )


def test_java_stack_preset_gates_every_delegated_project_command() -> None:
    preset = JAVA_PRESET.read_text(encoding="utf-8")

    assert "AI_COCKPIT_JAVA_LANE ?=" in preset
    assert "AI_COCKPIT_JAVA_REQUIRED_MAJOR ?=" in preset
    assert "ai_validate_java_runtime.py" in preset
    for command in ("./gradlew spotlessCheck", "./gradlew test", "./gradlew check"):
        assert f"AI_COCKPIT_JAVA_RUNTIME_CHECK) && {command}" in preset
