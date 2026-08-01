import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from ai_calibrate import CALIBRATION_STAGES
from ai_install_wizard import run_wizard
from ai_rollback import build_snapshot, execute_rollback, plan_rollback
from ai_uninstall_proposal import build_proposal

from scripts.ai_detached_uninstaller import prepare as prepare_detached_removal

ROOT = Path(__file__).resolve().parents[1]


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


@pytest.fixture(scope="module")
def japanese_adopter(tmp_path_factory):
    fixture_root = tmp_path_factory.mktemp("日本語採用プロジェクト")
    seed = fixture_root / "seed"
    remote = fixture_root / "日本語アプリ.git"
    target = fixture_root / "日本語アプリ"
    seed.mkdir()
    assert _run(seed, "git", "init", "-q", "-b", "main").returncode == 0
    assert _run(seed, "git", "config", "user.email", "test@example.invalid").returncode == 0
    assert _run(seed, "git", "config", "user.name", "Test").returncode == 0
    (seed / "README.md").write_text("# 日本語アプリ\n", encoding="utf-8")
    assert _run(seed, "git", "add", "README.md").returncode == 0
    assert _run(seed, "git", "commit", "-qm", "初期コミット").returncode == 0
    assert _run(seed, "git", "clone", "--bare", ".", str(remote)).returncode == 0
    assert _run(fixture_root, "git", "clone", "-q", str(remote), str(target)).returncode == 0
    assert _run(target, "git", "config", "user.email", "test@example.invalid").returncode == 0
    assert _run(target, "git", "config", "user.name", "Test").returncode == 0

    rendered: list[str] = []
    with pytest.MonkeyPatch.context() as environment:
        environment.setenv("AI_BASE_COMMIT", "f" * 40)
        environment.setenv("CONTRACT", "outer-template.contract.json")
        environment.setenv("SUMMARY", "outer-template.summary.json")
        environment.setenv("TASK", "outer-template-task")
        environment.setenv(
            "MAKEFLAGS",
            "-- CONTRACT=outer-template.contract.json PROJECT_TEST=true",
        )
        environment.setenv(
            "MAKEOVERRIDES",
            "AI_BASE_COMMIT=" + ("f" * 40) + " PROJECT_TEST=true",
        )
        result = run_wizard(
            target=target,
            source=ROOT,
            language="ja-JP",
            input_fn=iter(["1", "2", "y"]).__next__,
            output=rendered.append,
            is_tty=True,
        )
    assert result.status == "installed"
    return target, rendered


def test_japanese_adopter_installs_with_real_wizard_and_release_binding(japanese_adopter):
    target, rendered = japanese_adopter
    contract = json.loads(
        (target / ".ai/work-items/active/adopt_ai_cockpit.contract.json").read_text(
            encoding="utf-8"
        )
    )
    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))

    assert rendered[0] == "AI Cockpit インストール"
    assert "インストール方法を選択してください:" in rendered
    assert "ガバナンスプロファイルを選択してください (既定: Standard):" in rendered
    assert "インストールを実行しますか？ [y/N]" in rendered
    assert "インストール結果: installed (終了コード 0)。" in rendered
    assert _run(target, "git", "branch", "--show-current").stdout.strip() == "adopt/ai-cockpit"
    assert contract["sourceReleaseTag"] == release["releaseTag"]
    assert contract["sourceRepository"] == "local source"
    assert (target / ".ai/cockpit/adoption.ja.md").is_file()


def test_japanese_adopter_calibration_pauses_and_resumes(japanese_adopter):
    target, _ = japanese_adopter
    relative_session = ".ai/calibration/japanese-lifecycle.json"
    session_path = target / relative_session

    def calibrate(arguments: str) -> subprocess.CompletedProcess[str]:
        return _run(
            target,
            "make",
            "-f",
            "Makefile.ai",
            "cockpit-calibrate-session",
            f"ARGS={arguments} --session {relative_session}",
            f"PYTHON={sys.executable}",
        )

    started = calibrate("start --session-id japanese-lifecycle")
    assert started.returncode == 0, started.stdout + started.stderr
    answered = calibrate(
        "answer --stage repository_role --answer 日本語アプリ --answer-type alternative_input"
    )
    assert answered.returncode == 0, answered.stdout + answered.stderr
    paused = calibrate("pause")
    assert paused.returncode == 0, paused.stdout + paused.stderr
    assert json.loads(session_path.read_text(encoding="utf-8"))["state"] == "paused"
    resumed = calibrate("resume")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr

    session = json.loads(session_path.read_text(encoding="utf-8"))
    assert session["language"] == "ja"
    assert session["state"] == "in_progress"
    assert [stage["id"] for stage in session["stages"]] == list(CALIBRATION_STAGES)
    assert session["stages"][0]["checklist"]["answer"] == "日本語アプリ"


def test_japanese_adopter_recovery_is_confirmation_gated_and_preserves_project(
    japanese_adopter,
):
    target, _ = japanese_adopter
    project_config = {"path": str(target / "project-owned.yaml"), "language": "日本語"}
    snapshot = build_snapshot(
        "日本語-upgrade-1",
        {"manifestHash": "before"},
        {"version": "before"},
        {"runtime": ["scripts/ai_common.py"]},
        {"scripts/ai_common.py": "before"},
        project_config,
        {"rollback": "invertible"},
        ["ローカル検査を再実行する"],
    )
    current = {
        "manifestHash": "before",
        "runtime": {"scripts/ai_common.py": "after"},
    }
    proposal = plan_rollback(snapshot, current, project_config)

    assert proposal["state"] == "needs_human_confirmation"
    assert execute_rollback(snapshot, proposal, current, project_config)["writes"] == []
    drifted = plan_rollback(snapshot, {**current, "manifestHash": "after"}, project_config)
    assert drifted["state"] == "blocked"
    assert execute_rollback(snapshot, drifted, current, project_config)["writes"] == []

    recovered = execute_rollback(
        snapshot,
        proposal,
        current,
        project_config,
        confirm=True,
    )
    assert recovered["state"] == "rolled_back"
    assert recovered["stateAfter"]["runtime"]["scripts/ai_common.py"] == "before"
    assert recovered["projectConfig"] == project_config


def test_japanese_adopter_removal_blocks_unknown_ownership_and_preserves_evidence(
    japanese_adopter,
):
    _target, _ = japanese_adopter
    facts = {
        "sessionId": "日本語-removal-1",
        "runtimeFiles": ["scripts/ai_common.py", "README.md"],
        "projectOwned": ["README.md"],
    }
    blocked = build_proposal({**facts, "unknownOwnership": ["scripts/unknown.py"]})
    assert blocked["state"] == "blocked"
    assert blocked["writes"] == []

    proposal = build_proposal(facts, mode="preserve-evidence")
    assert proposal["state"] == "needs_human_confirmation"
    assert proposal["writes"] == []
    assert proposal["deletionList"] == ["scripts/ai_common.py"]
    assert proposal["evidenceExport"]["required"] is True

    detached = {
        "detached": True,
        "files": [
            "scripts/ai_common.py",
            "README.md",
            ".ai/upgrade/uninstall-evidence/日本語-removal-1.json",
        ],
        "preserve": [
            "README.md",
            ".ai/upgrade/uninstall-evidence/日本語-removal-1.json",
        ],
    }
    assert prepare_detached_removal("日本語-removal-1", detached)["writes"] == []
    removed = prepare_detached_removal("日本語-removal-1", detached, confirm=True)
    assert removed["state"] == "completed"
    assert removed["receipt"]["removed"] == ["scripts/ai_common.py"]
    assert removed["receipt"]["preserved"] == [
        "README.md",
        ".ai/upgrade/uninstall-evidence/日本語-removal-1.json",
    ]
    assert removed["receipt"]["evidencePreserved"] is True


def test_japanese_adopter_executes_installed_uninstall_lifecycle(japanese_adopter, tmp_path):
    target, _ = japanese_adopter
    isolated = tmp_path / "日本語採用先"
    shutil.copytree(target, isolated, symlinks=True)
    installed_executor = isolated / "scripts/ai_detached_uninstaller.py"
    assert "def execute_proposal" in installed_executor.read_text(encoding="utf-8")

    facts_path = "target/uninstall-facts.json"
    proposal_path = "target/uninstall-proposal.json"
    facts = _run(
        isolated,
        "make",
        "-f",
        "Makefile.ai",
        "ai-cockpit-uninstall-facts",
        "ROOT=.",
        "SESSION_ID=日本語-installed-lifecycle",
        f"OUTPUT={facts_path}",
        f"PYTHON={sys.executable}",
    )
    assert facts.returncode == 0, facts.stdout + facts.stderr
    proposal = _run(
        isolated,
        "make",
        "-f",
        "Makefile.ai",
        "ai-cockpit-uninstall-propose",
        f"FACTS={facts_path}",
        f"OUTPUT={proposal_path}",
        f"PYTHON={sys.executable}",
    )
    assert proposal.returncode == 0, proposal.stdout + proposal.stderr
    proposal_value = json.loads((isolated / proposal_path).read_text(encoding="utf-8"))
    assert proposal_value["state"] == "needs_human_confirmation"

    executed = _run(
        isolated,
        "make",
        "-f",
        "Makefile.ai",
        "ai-cockpit-uninstall-execute",
        "ROOT=.",
        f"PROPOSAL={proposal_path}",
        f"CONFIRM_DIGEST={proposal_value['proposalDigest']}",
        f"PYTHON={sys.executable}",
    )
    assert executed.returncode == 0, executed.stdout + executed.stderr
    receipt = isolated / ".ai/upgrade/uninstall-evidence/日本語-installed-lifecycle.receipt.json"
    result = json.loads(receipt.read_text(encoding="utf-8"))
    assert result["state"] == "completed"
    assert result["detachedExecution"] is True
    assert result["runtimeRemovalVerified"] is True
    assert (isolated / "README.md").is_file()
