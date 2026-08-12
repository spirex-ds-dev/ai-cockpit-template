import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ensure_locked_dev_environment as environment


def test_missing_virtual_environment_requires_provisioning(tmp_path: Path):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("ruff==0.16.0\n", encoding="utf-8")

    assert environment.needs_provision(
        tmp_path / ".venv" / "bin" / "python", manifest, root=tmp_path
    )


def test_mismatched_ruff_requires_provisioning(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "requirements-dev.in"
    manifest.write_text("ruff==0.16.0\n", encoding="utf-8")
    interpreter = tmp_path / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    interpreter.chmod(0o755)
    monkeypatch.setattr(environment, "installed_version", lambda *_args, **_kwargs: "0.15.21")

    assert environment.needs_provision(interpreter, manifest, root=tmp_path)


def test_provision_uses_hash_locked_install_and_converges(tmp_path: Path, monkeypatch):
    (tmp_path / "requirements-dev.lock").write_text("ruff==0.16.0\n", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run(command, *, cwd):
        commands.append(command)
        interpreter = tmp_path / ".venv" / "bin" / "python"
        interpreter.parent.mkdir(parents=True, exist_ok=True)
        interpreter.touch()
        interpreter.chmod(0o755)

    monkeypatch.setattr(environment, "run", fake_run)
    monkeypatch.setattr(environment, "needs_provision", lambda *_args, **_kwargs: False)

    environment.provision(tmp_path, "python3")

    assert commands == [
        ["python3", "-m", "venv", ".venv"],
        [
            str(tmp_path / ".venv" / "bin" / "python"),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            "requirements-dev.lock",
        ],
    ]


def test_quality_entrypoints_depend_on_locked_environment_provisioning():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert (
        "ensure-locked-dev-environment:\n\tpython3 scripts/ensure_locked_dev_environment.py --root ."
        in makefile
    )
    for target in (
        "quality-fast",
        "quality-standard",
        "quality-full",
        "quality-release",
        "check-quality-toolchain",
        "ai-start",
        "ai-preflight",
        "ai-finish",
        "check-ai-pr",
    ):
        assert f"{target}: ensure-locked-dev-environment" in makefile


def test_ensure_provisions_then_reports_the_verified_direct_pin(
    tmp_path: Path, monkeypatch, capsys
):
    (tmp_path / "requirements-dev.in").write_text("ruff==0.16.0\n", encoding="utf-8")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(environment, "needs_provision", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        environment,
        "provision",
        lambda root, bootstrap_python: calls.append(("provision", (root, bootstrap_python))),
    )
    monkeypatch.setattr(
        environment,
        "installed_version",
        lambda *_args, **_kwargs: "0.16.0",
    )

    environment.ensure(tmp_path, "python3")

    assert calls == [("provision", (tmp_path, "python3"))]
    assert "locked development environment provisioned: Ruff 0.16.0" in capsys.readouterr().out


def test_ensure_reuses_an_environment_that_already_matches_the_direct_pin(
    tmp_path: Path, monkeypatch, capsys
):
    (tmp_path / "requirements-dev.in").write_text("ruff==0.16.0\n", encoding="utf-8")
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(environment, "needs_provision", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        environment,
        "provision",
        lambda *_args, **_kwargs: calls.append(_args),
    )

    environment.ensure(tmp_path, "python3")

    assert calls == []
    assert "locked development environment ready: Ruff 0.16.0" in capsys.readouterr().out


def test_main_fails_closed_when_environment_cannot_be_provisioned(
    tmp_path: Path, monkeypatch, capsys
):
    monkeypatch.setattr(
        environment, "ensure", lambda *_args: (_ for _ in ()).throw(RuntimeError("offline"))
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ensure_locked_dev_environment.py",
            "--root",
            str(tmp_path),
            "--bootstrap-python",
            "python3",
        ],
    )

    assert environment.main() == 2
    assert "locked development environment unavailable: offline" in capsys.readouterr().err
