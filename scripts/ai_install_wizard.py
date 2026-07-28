"""Interactive, read-only-until-confirmed Installation Wizard orchestration."""

from __future__ import annotations

import argparse
import locale
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

from ai_install_plan import WizardPlan, build_wizard_plan
from ai_installer_detection import collect_installation_detection
from ai_wizard_io import confirm, select
from ai_wizard_localization import format_message, load_messages, resolve_language


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


def _render_plan(plan: WizardPlan, output: OutputFn, messages: dict[str, str]) -> None:
    for number, step in enumerate(plan.steps, 1):
        output(format_message(messages, "step_heading", number=number, name=step.name))
        output("  " + format_message(messages, "label_purpose", value=step.purpose))
        output("  " + format_message(messages, "label_why", value=step.why))
        output("  " + format_message(messages, "label_facts", value=step.facts))
        output("  " + format_message(messages, "label_suggested", value=step.suggested_value))
        output("  " + format_message(messages, "label_impact", value=step.option_impact))
        output("  " + format_message(messages, "label_example", value=step.example))
        output("  " + format_message(messages, "label_writes", value=step.write_status))
        output("  " + format_message(messages, "label_expected", value=step.expected_result))
        output("  " + format_message(messages, "label_stop", value=step.stop_condition))
        output("  " + format_message(messages, "label_checklist", value=", ".join(step.checklist)))


def _default_installer_factory(**kwargs: object) -> object:
    from install_ai_cockpit import Installer

    return cast(Any, Installer)(**kwargs)


def run_wizard(
    *,
    target: str | Path,
    source: str | Path,
    language: str | None = None,
    system_language: str | None = None,
    input_fn: Callable[[], str] = input,
    output: OutputFn = print,
    is_tty: bool = True,
    installer_factory: InstallerFactory = _default_installer_factory,
) -> WizardResult:
    """Run the eight-step wizard; target writes begin only after affirmative confirmation."""
    target_path = Path(target).resolve()
    source_path = Path(source).resolve()
    resolved_language = resolve_language(
        explicit=language,
        system_locale=system_language if system_language is not None else locale.getlocale()[0],
    )
    messages = load_messages(resolved_language)
    mode_options = (
        format_message(messages, "mode_new_adoption"),
        format_message(messages, "mode_upgrade"),
        format_message(messages, "mode_dry_run"),
    )
    output(format_message(messages, "installation_mode_prompt"))
    for number, option in enumerate(mode_options, 1):
        output(f"  {number}. {option}")
    mode_choice = select(mode_options, input_fn=input_fn, is_tty=is_tty)
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
    output(format_message(messages, "target", path=target_path))
    _render_plan(plan, output, messages)
    output(format_message(messages, "write_boundary"))
    output(format_message(messages, "automation_boundary"))

    if mode == "dry_run":
        output(format_message(messages, "dry_run_complete"))
        return WizardResult("dry_run", 0, plan, "read-only dry run")
    if detection.readiness == "blocked":
        output(format_message(messages, "installation_blocked"))
        return WizardResult("blocked", 2, plan, "readiness blocked")
    confirmation = format_message(messages, "confirm_installation")
    output(confirmation)
    if not confirm(confirmation, input_fn=input_fn, is_tty=is_tty):
        output(format_message(messages, "installation_cancelled"))
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
    output(
        format_message(
            messages,
            "installation_result",
            status=status,
            exit_code=exit_code,
        )
    )
    return WizardResult(status, exit_code, plan, status)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for direct scripted or TTY invocation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".")
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--language",
        help="Wizard language: ja, en, or zh-CN (default: environment, system locale, then ja)",
    )
    args = parser.parse_args(argv)
    try:
        result = run_wizard(
            target=args.target,
            source=args.source,
            language=args.language,
            is_tty=sys.stdin.isatty(),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
