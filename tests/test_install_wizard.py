from pathlib import Path

from ai_install_wizard import WizardResult, run_wizard


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
        input_fn=iter(["1", "y"]).__next__,
        output=lambda text: None,
        is_tty=True,
        installer_factory=FakeInstaller,
    )

    assert result.status == "installed"
    assert result.exit_code == 0
    assert calls and calls[0]["target"] == target
    assert calls[0]["dry_run"] is False
