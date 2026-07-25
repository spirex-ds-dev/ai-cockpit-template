import json
from pathlib import Path

import pytest

from ai_calibrate import CALIBRATION_STAGES, CalibrationError
from ai_calibration_wizard import CalibrationWizard


def wizard(tmp_path: Path) -> CalibrationWizard:
    return CalibrationWizard(
        tmp_path,
        tmp_path / ".ai/calibration/session.json",
        tmp_path / ".ai/calibration/active.json",
    )


def complete(wizard: CalibrationWizard) -> None:
    for stage in CALIBRATION_STAGES:
        wizard.answer(stage, "Y", answer_type="yes_no")


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
    complete(current)
    current.full_self_check()
    current.governance_simulation()
    with pytest.raises(CalibrationError, match="both human"):
        current.activate()
    current.confirm("reviewer")
    with pytest.raises(CalibrationError, match="both human"):
        current.activate()
    current.confirm("owner")
    with pytest.raises(CalibrationError, match="failed closed"):
        current.activate(fail=True)
    assert json.loads(active.read_text(encoding="utf-8")) == {"old": True}
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
