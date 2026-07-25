from __future__ import annotations

import json
from pathlib import Path

from ai_calibrate import CALIBRATION_STAGES
from ai_calibration_wizard import CalibrationWizard


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "wizard"
SNAPSHOTS = ROOT / "tests" / "snapshots" / "wizard"


def read(name: str, directory: Path) -> dict:
    return json.loads((directory / name).read_text(encoding="utf-8"))


def test_ios_fixture_matrix():
    fixture = read("ios.json", FIXTURES)
    assert fixture["language"] == "swift"
    assert {item["kind"] for item in fixture["projects"]} == {
        "swift_package",
        "xcode_project",
        "xcode_workspace",
        "cocoapods",
    }
    assert any(item["mode"] == "dry_run" for item in fixture["projects"])


def test_android_fixture_matrix():
    fixture = read("android.json", FIXTURES)
    kinds = {item["kind"] for item in fixture["projects"]}
    assert fixture["language"] == "kotlin"
    assert {"application", "multi_module", "flavor_variant", "jdk_and_tests"} <= kinds
    assert {signal for item in fixture["projects"] for signal in item["signals"]} >= {
        "JDK",
        "unit",
        "instrumented",
    }


def test_monorepo_and_upgrade_fixtures():
    fixture = read("monorepo.json", FIXTURES)
    kinds = {item["kind"] for item in fixture["projects"]}
    assert {
        "mobile_monorepo",
        "generic_mixed_monorepo",
        "dirty_worktree",
        "existing_runtime_upgrade",
    } <= kinds


def test_calibration_recovery_fixtures(tmp_path: Path):
    wizard = CalibrationWizard(tmp_path, tmp_path / "session.json", tmp_path / "active.json")
    wizard.load_or_start("fixture-resume")
    wizard.answer(CALIBRATION_STAGES[0], "Y", answer_type="yes_no")
    wizard.pause()
    resumed = CalibrationWizard(tmp_path, tmp_path / "session.json", tmp_path / "active.json")
    session = resumed.load_or_start()
    assert session.data["state"] == "paused"
    resumed.resume()
    assert resumed.session.data["stages"][0]["checklist"]["answer"] == "Y"


def test_snapshot_shapes():
    snapshots = [read(name, SNAPSHOTS) for name in ("swift.json", "kotlin.json", "mixed.json")]
    assert [item["language"] for item in snapshots] == ["swift", "kotlin", "mixed"]
    for snapshot in snapshots:
        assert snapshot["plan"]["write"] is False
        assert snapshot["checklist"]
        assert snapshot["result"] == {"status": "review_required", "activation": "not_run"}
