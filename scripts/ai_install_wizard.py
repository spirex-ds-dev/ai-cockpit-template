"""Interactive, read-only-until-confirmed Installation Wizard orchestration."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

from ai_install_plan import WizardPlan, build_wizard_plan
from ai_installer_detection import collect_installation_detection
from ai_wizard_io import confirm, select


OutputFn = Callable[[str], None]
InstallerFactory = Callable[..., object]


@dataclass(frozen=True)
class WizardResult:
    """Stable result returned by a wizard session."""

    status: str
    exit_code: int
    plan: WizardPlan | None = None
    message: str = ""


def detect_stack_signals(target: Path) -> tuple[str, ...]:
    """Infer stack labels from names without changing the target repository."""
    names = {path.name for path in target.iterdir()} if target.is_dir() else set()
    stacks: set[str] = set()
    if {"pyproject.toml", "setup.py", "requirements.txt"} & names:
        stacks.add("python")
    if (
        {"Package.swift", "Podfile"} & names
        or any(target.glob("*.xcodeproj"))
        or any(target.glob("*.xcworkspace"))
    ):
        stacks.add("swift")
    if {"settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"} & names or (
        target / "gradlew"
    ).exists():
        stacks.add("android")
    return tuple(sorted(stacks or {"generic"}))


def _render_plan(plan: WizardPlan, output: OutputFn) -> None:
    for number, step in enumerate(plan.steps, 1):
        output(f"Step {number}/8: {step.name}")
        output(f"  Purpose: {step.purpose}")
        output(f"  Why: {step.why}")
        output(f"  Facts: {step.facts}")
        output(f"  Suggested: {step.suggested_value}")
        output(f"  Impact: {step.option_impact}")
        output(f"  Example: {step.example}")
        output(f"  Writes: {step.write_status}")
        output(f"  Expected: {step.expected_result}")
        output(f"  Stop: {step.stop_condition}")
        output(f"  Checklist: {', '.join(step.checklist)}")


def _default_installer_factory(**kwargs: object) -> object:
    from install_ai_cockpit import Installer

    return cast(Any, Installer)(**kwargs)


def run_wizard(
    *,
    target: str | Path,
    source: str | Path,
    input_fn: Callable[[], str] = input,
    output: OutputFn = print,
    is_tty: bool = True,
    installer_factory: InstallerFactory = _default_installer_factory,
) -> WizardResult:
    """Run the eight-step wizard; target writes begin only after affirmative confirmation."""
    target_path = Path(target).resolve()
    source_path = Path(source).resolve()
    mode_choice = select(("New Adoption", "Upgrade", "Dry Run"), input_fn=input_fn, is_tty=is_tty)
    if not isinstance(mode_choice, int):
        return WizardResult("cancelled", 1, message="mode selection cancelled")
    mode = ("new_adoption", "upgrade", "dry_run")[mode_choice]
    detection_mode = "upgrade" if mode == "upgrade" else "new_adoption"
    stacks = detect_stack_signals(target_path)
    detection = collect_installation_detection(target_path, mode=detection_mode, stacks=stacks)
    stack = stacks[0] if len(stacks) == 1 else "multi"
    options = {
        "force": False,
        "with_examples": False,
        "update_makefile": False,
        "stacks": list(stacks),
    }
    branch = detection.facts.default_branch or detection.facts.branch or "main"
    plan = build_wizard_plan(detection, stack=stack, options=options, branch=branch)
    _render_plan(plan, output)
    output("Write boundary: no target writes before final confirmation.")
    output("Automation: no commit / no push / no PR / no merge.")

    if mode == "dry_run":
        output("Dry Run complete: target repository remains unchanged.")
        return WizardResult("dry_run", 0, plan, "read-only dry run")
    if detection.readiness == "blocked":
        output("Installation blocked: readiness facts require resolution before confirmation.")
        return WizardResult("blocked", 2, plan, "readiness blocked")
    if not confirm("Confirm installation? [y/N]", input_fn=input_fn, is_tty=is_tty):
        output("Installation cancelled; target repository remains unchanged.")
        return WizardResult("cancelled", 1, plan, "confirmation declined")

    installer = installer_factory(
        source=source_path,
        target=target_path,
        stack=stack if stack != "multi" else "generic",
        force=bool(options["force"]),
        dry_run=False,
        with_examples=bool(options["with_examples"]),
        update_makefile=bool(options["update_makefile"]),
        upgrade=mode == "upgrade",
        upgrade_with_active=False,
        replace_glossary=False,
        create_adoption=mode == "new_adoption",
        base_remote=detection.facts.remote,
        base_branch=branch,
        confirm_upgrade_conflicts=False,
    )
    exit_code = int(installer.install())  # type: ignore[attr-defined]
    status = "installed" if exit_code == 0 else "failed"
    output(f"Installation result: {status} (exit code {exit_code}).")
    return WizardResult(status, exit_code, plan, status)


def main() -> int:
    """CLI entry point for direct scripted or TTY invocation."""
    result = run_wizard(
        target=Path.cwd(), source=Path(__file__).resolve().parents[1], is_tty=sys.stdin.isatty()
    )
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
