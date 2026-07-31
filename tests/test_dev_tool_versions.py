from types import SimpleNamespace

import check_dev_tool_versions
import pytest


def test_direct_pin_reads_exact_tool_version(tmp_path):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("pytest==9.1.1\nruff==0.16.0\n", encoding="utf-8")

    assert check_dev_tool_versions.direct_pin(manifest, "ruff") == "0.16.0"


def test_direct_pin_rejects_missing_or_ambiguous_tool(tmp_path):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("pytest==9.1.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one direct pin"):
        check_dev_tool_versions.direct_pin(manifest, "ruff")

    manifest.write_text("ruff==0.15.21\nruff==0.16.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one direct pin"):
        check_dev_tool_versions.direct_pin(manifest, "ruff")


def test_installed_version_uses_current_python_module(monkeypatch):
    monkeypatch.setattr(
        check_dev_tool_versions.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="ruff 0.16.0\n",
            stderr="",
        ),
    )

    assert check_dev_tool_versions.installed_version("ruff") == "0.16.0"


def test_check_tool_version_fails_closed_on_mismatch(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("ruff==0.16.0\n", encoding="utf-8")
    monkeypatch.setattr(check_dev_tool_versions, "installed_version", lambda _tool: "0.15.21")

    assert check_dev_tool_versions.check_tool_version(manifest, "ruff") == 1
    error = capsys.readouterr().err
    assert "expected 0.16.0" in error
    assert "observed 0.15.21" in error
    assert "locked development environment" in error


def test_check_tool_version_accepts_exact_match(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("ruff==0.16.0\n", encoding="utf-8")
    monkeypatch.setattr(check_dev_tool_versions, "installed_version", lambda _tool: "0.16.0")

    assert check_dev_tool_versions.check_tool_version(manifest, "ruff") == 0
    assert "ruff version check passed: 0.16.0" in capsys.readouterr().out


def test_command_line_rejects_an_arbitrary_python_module(monkeypatch):
    monkeypatch.setattr(check_dev_tool_versions.sys, "argv", ["check", "--tool", "pytest"])

    with pytest.raises(SystemExit, match="2"):
        check_dev_tool_versions.main()
