#!/usr/bin/env python3
"""Interactive adapter for the durable ten-stage calibration session.

The wizard owns presentation and navigation only.  CalibrationSession remains
the single authority for persistence, validation, checks, confirmations, and
atomic Candidate Activation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from ai_calibrate import (
    ANSWER_TYPES,
    CALIBRATION_STAGES,
    CalibrationError,
    CalibrationSession,
    generate,
    load_session,
    save_session,
)
from ai_project_doctor import scan_project


STAGES = CALIBRATION_STAGES
ANSWER_PROMPTS = {
    "yes_no": "Y/N",
    "alternative_input": "Input",
    "unknown": "Unknown",
    "not_applicable": "N/A (reason required)",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SECRET_VALUE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|passwd|private[_-]?key)\s*[:=]\s*[^\s,;]+"
)


class CalibrationWizard:
    """Presentation and orchestration adapter around :class:`CalibrationSession`."""

    def __init__(self, root: Path, session_path: Path, active_path: Path) -> None:
        self.root = root.resolve()
        self.session_path = session_path
        self.active_path = active_path
        self.session: CalibrationSession | None = None

    def load_or_start(self, session_id: str = "calibration-1") -> CalibrationSession:
        if not IDENTIFIER.fullmatch(session_id):
            raise CalibrationError("session_id contains invalid characters")
        if self.session_path.is_file():
            self.session = load_session(self.session_path)
        else:
            self.session = CalibrationSession.start(session_id)
            save_session(self.session, self.session_path)
        return self.session

    def persist(self) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        save_session(self.session, self.session_path)

    def doctor_report(self) -> dict[str, Any]:
        """Return read-only Project Doctor facts and persist the prescribed report."""
        report = scan_project(self.root)
        output = self.root / "target" / "ai_project_doctor_report.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report

    def prepare_proposal(self) -> Path:
        report_path = self.root / "target" / "ai_project_doctor_report.json"
        if not report_path.is_file():
            self.doctor_report()
        proposal = self.root / ".ai" / "project_profile.proposed.yaml"
        if not proposal.exists():
            if generate(self.root, report_path, proposal) != 0:
                raise CalibrationError("failed to generate calibration proposal")
        return proposal

    def answer(
        self, stage: str, answer: str, *, answer_type: str = "alternative_input", reason: str = ""
    ) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self._validate_stage(stage)
        self.session.answer(
            stage,
            self._redact(answer),
            answer_type=answer_type,
            reason=self._redact(reason),
        )
        self.persist()

    @staticmethod
    def _redact(value: str) -> str:
        return SECRET_VALUE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)

    @staticmethod
    def _validate_stage(stage: str) -> None:
        if stage not in STAGES:
            raise CalibrationError("invalid calibration stage identifier")

    def blocking_unknowns(self) -> list[str]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        return [
            stage["id"]
            for stage in self.session.data["stages"]
            if stage.get("checklist", {}).get("answerType") == "unknown"
        ]

    def revalidate(self) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.revalidate()
        self.persist()

    def back(self) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.back()
        self.persist()

    def pause(self) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.pause()
        self.persist()

    def resume(self) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.resume()
        self.persist()

    def stage_self_check(self) -> dict[str, Any]:
        return self._checked("stage_self_check")

    def full_self_check(self) -> dict[str, Any]:
        result = self._checked("full_self_check")
        return self._apply_blocking_guard(result)

    def governance_simulation(self) -> dict[str, Any]:
        result = self._checked("governance_simulation")
        return self._apply_blocking_guard(result)

    def _apply_blocking_guard(self, result: dict[str, Any]) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        blockers = self.blocking_unknowns() + list(self.session.data.get("staleStages", []))
        if blockers:
            result = {**result, "status": "blocked", "blockingStages": sorted(set(blockers))}
            self.session.data.setdefault("checks", {})[result["evidence"]["kind"]] = result
            self.persist()
        return result

    def review(self) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        result = self.session.review()
        blockers = self.blocking_unknowns() + list(self.session.data.get("staleStages", []))
        if blockers:
            result = {**result, "status": "blocked", "blockingStages": sorted(set(blockers))}
            self.session.data["review"] = result
        self.persist()
        return result

    def _checked(self, operation: str) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        result = getattr(self.session, operation)()
        self.persist()
        return result

    def confirm(self, phase: str) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.confirm(phase)
        self.persist()

    def activate(self, *, fail: bool = False) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        if self.blocking_unknowns() or self.session.data.get("staleStages"):
            raise CalibrationError("blocking Unknown or stale evidence requires revalidation")
        if self.session.data.get("checks", {}).get("full_self_check", {}).get("status") != "passed":
            raise CalibrationError("full self-check must pass before activation")
        if (
            self.session.data.get("checks", {}).get("governance_simulation", {}).get("status")
            != "passed"
        ):
            raise CalibrationError("governance simulation must pass before activation")
        self.session.activate(active_path=self.active_path, fail=fail)
        self.persist()

    def render(self) -> str:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        lines = ["Calibration Wizard / 校准向导", ""]
        for stage in self.session.data["stages"]:
            current = " *" if stage["id"] == self.session.data.get("currentStage") else ""
            lines.append(
                f"{stage['position'] + 1:02d}. {stage['id']} [{stage['status']}]" + current
            )
            lines.append("    answers: " + ", ".join(ANSWER_PROMPTS[k] for k in ANSWER_TYPES))
        lines.append(f"state: {self.session.data['state']}")
        lines.append("Unknown remains explicit; N/A requires a reason.")
        return "\n".join(lines)

    def run(
        self, input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print
    ) -> int:
        """Run a safe terminal loop; EOF/Ctrl+C pauses and returns without activation."""
        self.load_or_start()
        self.doctor_report()
        self.prepare_proposal()
        output_fn(self.render())
        while self.session and self.session.data.get("state") == "in_progress":
            try:
                command = (
                    input_fn("command (answer/back/check/review/pause/quit): ").strip().lower()
                )
            except (EOFError, KeyboardInterrupt):
                self.pause()
                output_fn("Paused; resume with the same session file.")
                return 0
            if command in {"quit", "q", "pause"}:
                self.pause()
                output_fn("Paused; no activation performed.")
                return 0
            if command == "back":
                self.back()
            elif command == "check":
                output_fn(json.dumps(self.stage_self_check(), ensure_ascii=False))
            elif command == "review":
                output_fn(json.dumps(self.review(), ensure_ascii=False))
            elif command == "answer":
                stage = self.session.data.get("currentStage")
                if not stage:
                    output_fn("No current stage; use review.")
                    continue
                value = input_fn("answer: ")
                self.answer(stage, value)
            else:
                output_fn("Unknown command; session remains unchanged.")
            output_fn(self.render())
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--session", default=".ai/calibration/session.json")
    parser.add_argument("--active", default=".ai/calibration/active.json")
    parser.add_argument("--session-id", default="calibration-1")
    parser.add_argument(
        "--summary", action="store_true", help="render the current wizard state and exit"
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    wizard = CalibrationWizard(root, root / args.session, root / args.active)
    try:
        wizard.load_or_start(args.session_id)
        if args.summary:
            print(wizard.render())
            return 0
        return wizard.run()
    except CalibrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
