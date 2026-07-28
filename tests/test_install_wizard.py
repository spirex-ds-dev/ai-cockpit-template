from pathlib import Path
from dataclasses import replace

import pytest

import ai_install_wizard
from ai_install_wizard import WizardResult, main, run_wizard
from ai_installer_detection import collect_installation_detection


def test_cancel_before_confirmation_does_not_invoke_installer(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    calls: list[object] = []

    def installer_factory(**kwargs: object) -> object:
        calls.append(kwargs)
        raise AssertionError("installer must not run before confirmation")

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="en",
        input_fn=iter(["1", "n"]).__next__,
        output=lambda text: None,
        is_tty=True,
        installer_factory=installer_factory,
    )

    assert isinstance(result, WizardResult)
    assert result.status == "cancelled"
    assert calls == []
    assert list(target.iterdir()) == []


def test_dry_run_is_read_only_and_reports_all_steps(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    rendered: list[str] = []

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="en",
        input_fn=iter(["3"]).__next__,
        output=rendered.append,
        is_tty=True,
    )

    assert result.status == "dry_run"
    assert result.plan is not None
    assert [step.name for step in result.plan.steps] == [
        "Target Repository",
        "Repository Readiness",
        "Installation Mode",
        "Project Stack",
        "Installation Options",
        "Adoption Branch",
        "Installation Plan Review",
        "Installation/Result",
    ]
    assert not list(target.iterdir())
    assert any("no commit / no push / no PR / no merge" in line for line in rendered)


def test_confirmation_delegates_to_existing_installer(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    calls: list[dict[str, object]] = []

    class FakeInstaller:
        def __init__(self, **kwargs: object) -> None:
            calls.append(kwargs)

        def install(self) -> int:
            return 0

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="en",
        input_fn=iter(["1", "y"]).__next__,
        output=lambda text: None,
        is_tty=True,
        installer_factory=FakeInstaller,
    )

    assert result.status == "installed"
    assert result.exit_code == 0
    assert calls and calls[0]["target"] == target
    assert calls[0]["dry_run"] is False


def test_japanese_dry_run_uses_executable_locale_resources(tmp_path: Path) -> None:
    target = tmp_path / "日本語アプリ"
    target.mkdir()
    rendered: list[str] = []

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="ja-JP",
        input_fn=iter(["3"]).__next__,
        output=rendered.append,
        is_tty=True,
    )

    assert result.status == "dry_run"
    assert rendered[0] == "インストール方法を選択してください:"
    assert "  3. ドライラン" in rendered
    assert any("対象リポジトリ" in line and str(target) in line for line in rendered)
    assert any("対象リポジトリは変更されていません" in line for line in rendered)
    assert any("commit / push / PR / merge は実行しません" in line for line in rendered)


def test_japanese_decline_preserves_fail_closed_write_boundary(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    rendered: list[str] = []
    calls: list[object] = []

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="ja",
        input_fn=iter(["1", "n"]).__next__,
        output=rendered.append,
        is_tty=True,
        installer_factory=lambda **kwargs: calls.append(kwargs),
    )

    assert result.status == "cancelled"
    assert calls == []
    assert "インストールを実行しますか？ [y/N]" in rendered
    assert any("インストールを中止しました" in line for line in rendered)


def test_install_wizard_unknown_language_fails_before_target_write(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    with pytest.raises(ValueError, match="unsupported language"):
        run_wizard(
            target=target,
            source=tmp_path,
            language="fr",
            input_fn=iter(["3"]).__next__,
            output=lambda _: None,
            is_tty=True,
        )

    assert list(target.iterdir()) == []


def test_japanese_blocked_readiness_stops_before_installer(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    detection = collect_installation_detection(
        target,
        mode="new_adoption",
        stacks=("generic",),
    )
    monkeypatch.setattr(
        ai_install_wizard,
        "collect_installation_detection",
        lambda *args, **kwargs: replace(detection, readiness="blocked"),
    )
    rendered: list[str] = []
    calls: list[object] = []

    result = run_wizard(
        target=target,
        source=tmp_path,
        language="ja",
        input_fn=iter(["1"]).__next__,
        output=rendered.append,
        is_tty=True,
        installer_factory=lambda **kwargs: calls.append(kwargs),
    )

    assert result.status == "blocked"
    assert result.exit_code == 2
    assert calls == []
    assert any("インストールを停止しました" in line for line in rendered)


def test_install_wizard_cli_exposes_language_and_rejects_unknown(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0
    assert "--language" in capsys.readouterr().out

    assert main(["--language", "fr"]) == 2
    assert "unsupported language: fr" in capsys.readouterr().err
