import json
from pathlib import Path

import pytest

from ai_calibrate import CALIBRATION_STAGES, CalibrationError
from ai_calibration_wizard import CalibrationWizard, main


def wizard(tmp_path: Path) -> CalibrationWizard:
    return CalibrationWizard(
        tmp_path,
        tmp_path / ".ai/calibration/session.json",
        tmp_path / ".ai/calibration/active.json",
        language="en",
    )


def complete(wizard: CalibrationWizard) -> None:
    for stage in CALIBRATION_STAGES:
        wizard.answer(stage, "Y", answer_type="yes_no")
        wizard.record_checklist_evidence(
            stage,
            observed_evidence=[f"evidence/{stage}.txt"],
            candidate_change=f"no change: {stage} is evidenced",
            owner="repository-owner",
            reviewer="repository-reviewer",
            decision="PASS",
            decision_reason=f"{stage} evidence is complete",
        )


def prepared(wizard: CalibrationWizard) -> dict[str, object]:
    complete(wizard)
    assert wizard.review()["status"] == "ready"
    assert wizard.full_self_check()["status"] == "passed"
    assert wizard.governance_simulation()["status"] == "passed"
    return wizard.prepare_candidate()


def confirm(wizard: CalibrationWizard, phase: str, candidate: dict[str, object]) -> None:
    wizard.confirm(
        phase,
        candidate_revision=int(candidate["revision"]),
        candidate_digest=str(candidate["digest"]),
    )


def test_fixed_stage_order(tmp_path: Path):
    current = wizard(tmp_path)
    session = current.load_or_start("fixed")
    assert tuple(stage["id"] for stage in session.data["stages"]) == CALIBRATION_STAGES
    assert len(session.data["stages"]) == 10
    assert "Unknown" in current.render()
    assert "N/A (reason required)" in current.render()


def test_pause_and_resume_preserves_session(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("resume")
    current.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    current.pause()
    resumed = wizard(tmp_path)
    session = resumed.load_or_start("ignored")
    assert session.data["state"] == "paused"
    assert session.data["stages"][0]["checklist"]["answer"] == "Y"
    resumed.resume()
    resumed.answer(CALIBRATION_STAGES[1], "Python")
    assert resumed.session.data["stages"][1]["checklist"]["answer"] == "Python"


def test_back_navigation(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start()
    current.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    current.back()
    assert current.session.data["currentStage"] == CALIBRATION_STAGES[0]
    assert any(event["kind"] == "back" for event in current.session.data["events"])


def test_self_check_and_simulation(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start()
    assert current.stage_self_check()["status"] == "blocked"
    complete(current)
    assert current.full_self_check()["status"] == "passed"
    assert current.governance_simulation()["status"] == "passed"
    assert current.review()["status"] == "ready"


def test_separate_confirmations_and_activation_failure(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("activation")
    active = current.active_path
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text('{"old": true}\n', encoding="utf-8")
    candidate = prepared(current)
    with pytest.raises(CalibrationError, match="both human"):
        current.activate()
    confirm(current, "reviewer", candidate)
    with pytest.raises(CalibrationError, match="both human"):
        current.activate()
    confirm(current, "owner", candidate)
    current.activate()
    assert json.loads(active.read_text(encoding="utf-8"))["sessionId"] == "activation"


def test_not_applicable_requires_reason(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start()
    with pytest.raises(CalibrationError, match="requires a reason"):
        current.answer(CALIBRATION_STAGES[0], "N/A", answer_type="not_applicable")


def test_doctor_and_proposal_are_reused_as_evidence(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("evidence")
    report = current.doctor_report()
    assert report["reportVersion"] == 1
    proposal = current.prepare_proposal()
    assert proposal == tmp_path / ".ai/project_profile.proposed.yaml"
    assert proposal.is_file()


def test_blocking_unknown_fails_closed(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("blocking")
    current.answer(CALIBRATION_STAGES[0], "unknown", answer_type="unknown")
    assert current.blocking_unknowns() == [CALIBRATION_STAGES[0]]
    assert current.full_self_check()["status"] == "blocked"
    with pytest.raises(CalibrationError, match="blocking calibration evidence"):
        current.activate()


def test_stale_session_requires_revalidation(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("stale")
    current.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    current.answer(CALIBRATION_STAGES[1], "Python")
    current.answer(CALIBRATION_STAGES[2], "src")
    current.back()
    current.answer(CALIBRATION_STAGES[1], "TypeScript")
    assert current.session.data["staleStages"]
    with pytest.raises(CalibrationError, match="blocking calibration evidence.*stale"):
        current.activate()
    current.revalidate()
    assert current.session.data["staleStages"] == []
    assert current.session.data["currentStage"] == CALIBRATION_STAGES[2]


def test_interrupt_and_quit_pause_safely(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("interrupt")

    def eof(_: str) -> str:
        raise EOFError

    assert current.run(input_fn=eof, output_fn=lambda _: None) == 0
    assert current.session.data["state"] == "paused"
    resumed = wizard(tmp_path)
    resumed.load_or_start()
    assert resumed.session.data["state"] == "paused"


def test_command_loop_covers_checks_navigation_and_safe_pause(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("commands")
    current.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    commands = iter(["check", "review", "back", "unknown", "pause"])
    output: list[str] = []

    def input_fn(_: str) -> str:
        return next(commands)

    assert current.run(input_fn=input_fn, output_fn=output.append) == 0
    assert current.session.data["state"] == "paused"
    assert any('"status": "blocked"' in item for item in output)
    assert any("Unknown command" in item for item in output)
    assert any("no activation performed" in item for item in output)


def test_command_loop_answers_current_stage(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("answer-command")
    inputs = iter(["answer", "Y", "pause"])

    def input_fn(_: str) -> str:
        return next(inputs)

    assert current.run(input_fn=input_fn, output_fn=lambda _: None) == 0
    assert current.session.data["stages"][0]["checklist"]["answer"] == "Y"
    assert current.session.data["state"] == "paused"


def test_secret_values_are_redacted(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("secrets")
    current.answer(CALIBRATION_STAGES[0], "token=super-secret", answer_type="alternative_input")
    raw = current.session_path.read_text(encoding="utf-8")
    assert "super-secret" not in raw
    assert "[REDACTED]" in raw
    assert "super-secret" not in current.render()


def test_activation_failure_preserves_active(tmp_path: Path):
    current = wizard(tmp_path)
    current.load_or_start("failure")
    current.active_path.parent.mkdir(parents=True, exist_ok=True)
    current.active_path.write_text('{"original": true}\n', encoding="utf-8")
    candidate = prepared(current)
    confirm(current, "reviewer", candidate)
    confirm(current, "owner", candidate)
    real_replace = __import__("os").replace
    failed = False

    def fail_session_replace(source: str | Path, destination: str | Path) -> None:
        nonlocal failed
        if Path(destination) == current.session_path and not failed:
            failed = True
            raise OSError("simulated Session replace failure")
        real_replace(source, destination)

    with pytest.raises(CalibrationError, match="Active and Session restored"):
        current.activate(replace_fn=fail_session_replace)
    assert json.loads(current.active_path.read_text(encoding="utf-8")) == {"original": True}


def test_japanese_render_and_pause_use_executable_locale_resources(tmp_path: Path):
    current = CalibrationWizard(
        tmp_path,
        tmp_path / ".ai/calibration/session.json",
        tmp_path / ".ai/calibration/active.json",
        language="ja-JP",
    )
    current.load_or_start("ja-session")
    rendered = current.render()

    assert rendered.startswith("校正ウィザード")
    assert "状態: in_progress" in rendered
    assert "セッション:" in rendered
    assert "不明は明示したまま" in rendered
    assert "repository_role" in rendered

    prompts: list[str] = []
    output: list[str] = []

    def pause(prompt: str) -> str:
        prompts.append(prompt)
        return "pause"

    assert current.run(input_fn=pause, output_fn=output.append) == 0
    assert prompts == ["操作を選択してください (answer/back/check/review/pause/quit): "]
    assert any("一時停止しました。Activation は実行していません。" in line for line in output)


def test_japanese_unknown_command_and_answer_prompt(tmp_path: Path):
    current = CalibrationWizard(
        tmp_path,
        tmp_path / ".ai/calibration/session.json",
        tmp_path / ".ai/calibration/active.json",
        language="ja",
    )
    current.load_or_start("commands-ja")
    prompts: list[str] = []
    output: list[str] = []
    commands = iter(["unknown-command", "answer", "Y", "pause"])

    def input_fn(prompt: str) -> str:
        prompts.append(prompt)
        return next(commands)

    assert current.run(input_fn=input_fn, output_fn=output.append) == 0
    assert any("不明な操作です" in line for line in output)
    assert "回答: " in prompts


def test_calibration_cli_exposes_language_and_rejects_unknown(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0
    assert "--language" in capsys.readouterr().out

    assert main(["--language", "fr"]) == 2
    assert "unsupported language: fr" in capsys.readouterr().err


def test_calibration_cli_japanese_summary(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "--language", "ja", "--summary"]) == 0

    rendered = capsys.readouterr().out
    assert rendered.startswith("校正ウィザード")
    assert "状態: in_progress" in rendered
