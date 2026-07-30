#!/usr/bin/env python3
"""Interactive adapter for the durable ten-stage calibration session.

The wizard owns presentation and navigation only.  CalibrationSession remains
the single authority for persistence, validation, checks, confirmations, and
atomic Candidate Activation.
"""

from __future__ import annotations

import argparse
import json
import locale
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ai_calibrate import (
    ANSWER_TYPES,
    CALIBRATION_STAGES,
    CalibrationError,
    CalibrationSession,
    generate,
    load_session,
    persist_activation,
    save_session,
)
from ai_project_doctor import scan_project
from ai_wizard_localization import format_message, load_messages, resolve_language

STAGES = CALIBRATION_STAGES
ANSWER_PROMPT_KEYS = {
    "yes_no": "answer_yes_no",
    "alternative_input": "answer_input",
    "unknown": "answer_unknown",
    "not_applicable": "answer_na",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SECRET_VALUE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|passwd|private[_-]?key)\s*[:=]\s*[^\s,;]+"
)


class CalibrationWizard:
    """Presentation and orchestration adapter around :class:`CalibrationSession`."""

    def __init__(
        self,
        root: Path,
        session_path: Path,
        active_path: Path,
        *,
        language: str | None = None,
        system_language: str | None = None,
    ) -> None:
        self.root = root.resolve()
        self.session_path = session_path
        self.active_path = active_path
        self.session: CalibrationSession | None = None
        self.language = resolve_language(
            explicit=language,
            system_locale=system_language if system_language is not None else locale.getlocale()[0],
        )
        self.messages = load_messages(self.language)

    def message(self, key: str, **values: object) -> str:
        """Render locale chrome without changing evidence-bearing values."""
        return format_message(self.messages, key, **values)

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
        if not proposal.exists() and generate(self.root, report_path, proposal) != 0:
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

    def record_checklist_evidence(
        self,
        stage: str,
        *,
        observed_evidence: list[str],
        candidate_change: str,
        owner: str,
        reviewer: str,
        decision: str,
        decision_reason: str,
        retry_step: str = "",
    ) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self._validate_stage(stage)
        self.session.record_checklist_evidence(
            stage,
            observed_evidence=[self._redact(item) for item in observed_evidence],
            candidate_change=self._redact(candidate_change),
            owner=self._redact(owner),
            reviewer=self._redact(reviewer),
            decision=decision,
            decision_reason=self._redact(decision_reason),
            retry_step=self._redact(retry_step),
        )
        self.persist()

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
        return self._checked("full_self_check")

    def governance_simulation(self) -> dict[str, Any]:
        return self._checked("governance_simulation")

    def review(self) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        result = self.session.review()
        self.persist()
        return result

    def _checked(self, operation: str) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        result = getattr(self.session, operation)()
        self.persist()
        return result

    def prepare_candidate(self) -> dict[str, Any]:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        candidate = self.session.prepare_candidate()
        self.persist()
        return candidate

    def confirm(
        self,
        phase: str,
        *,
        candidate_revision: int,
        candidate_digest: str,
    ) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        self.session.confirm(
            phase,
            candidate_revision=candidate_revision,
            candidate_digest=candidate_digest,
        )
        self.persist()

    def activate(
        self,
        *,
        replace_fn: Callable[[str | Path, str | Path], None] = os.replace,
    ) -> None:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        persist_activation(
            self.session,
            session_path=self.session_path,
            active_path=self.active_path,
            replace_fn=replace_fn,
        )

    def render(self) -> str:
        if self.session is None:
            raise CalibrationError("wizard session has not been loaded")
        lines = [self.message("calibration_title"), ""]
        for stage in self.session.data["stages"]:
            current = " *" if stage["id"] == self.session.data.get("currentStage") else ""
            lines.append(
                f"{stage['position'] + 1:02d}. {stage['id']} [{stage['status']}]" + current
            )
            answer_labels = ", ".join(self.message(ANSWER_PROMPT_KEYS[key]) for key in ANSWER_TYPES)
            lines.append("    " + self.message("label_answers", value=answer_labels))
        lines.append(self.message("label_state", value=self.session.data["state"]))
        lines.append(self.message("label_session", value=self.session_path))
        candidate = self.session.data.get("candidate", {})
        lines.append(
            self.message(
                "label_candidate",
                status=candidate.get("status"),
                revision=candidate.get("revision"),
                digest=candidate.get("digest") or "not_prepared",
            )
        )
        blockers = self.session.blocking_fields()
        if blockers:
            lines.append(
                self.message(
                    "label_blocking",
                    value=json.dumps(blockers, ensure_ascii=False),
                )
            )
        lines.append(self.message("unknown_na_boundary"))
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
                command = input_fn(self.message("command_prompt")).strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.pause()
                output_fn(self.message("paused_resume"))
                return 0
            if command in {"quit", "q", "pause"}:
                self.pause()
                output_fn(self.message("paused_no_activation"))
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
                    output_fn(self.message("no_current_stage"))
                    continue
                value = input_fn(self.message("answer_prompt"))
                self.answer(stage, value)
            else:
                output_fn(self.message("unknown_command"))
            output_fn(self.render())
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--session", default=".ai/calibration/session.json")
    parser.add_argument("--active", default=".ai/calibration/active.json")
    parser.add_argument("--session-id", default="calibration-1")
    parser.add_argument(
        "--language",
        help="Wizard language: ja, en, or zh-CN (default: environment, system locale, then ja)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="render the current wizard state and exit"
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        wizard = CalibrationWizard(
            root,
            root / args.session,
            root / args.active,
            language=args.language,
        )
        wizard.load_or_start(args.session_id)
        if args.summary:
            print(wizard.render())
            return 0
        return wizard.run()
    except (CalibrationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2 if isinstance(exc, ValueError) else 1


if __name__ == "__main__":
    raise SystemExit(main())
