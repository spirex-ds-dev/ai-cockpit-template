import subprocess
import json
from pathlib import Path

import pytest

from install_ai_cockpit import Installer


ROOT = Path(__file__).resolve().parents[1]


def test_installed_distribution_contains_pr_and_approval_wiring(tmp_path):
    installer = Installer(
        source=ROOT,
        target=tmp_path,
        stack="generic",
        force=False,
        dry_run=False,
        with_examples=False,
        update_makefile=True,
    )

    assert installer.install() == 0
    assert (tmp_path / "scripts" / "ai_check_pr.py").is_file()
    assert "<!-- AI_COCKPIT_SECTION -->" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert not list((tmp_path / ".ai" / "work-items" / "active").glob("*.json"))
    assert not list((tmp_path / ".ai" / "work-items" / "archive").rglob("*.json"))
    assert "- State: `no_active_work_item`" in (
        tmp_path / ".ai" / "cockpit" / "current_status.md"
    ).read_text(encoding="utf-8")
    assert ".ai/work-items/active/*.contract.json" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".ai/work-items/active/*.review.json" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".ai/cockpit/upgrade-backups/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    makefile_ai = (tmp_path / "Makefile.ai").read_text(encoding="utf-8")
    assert "check-ai-pr:" in makefile_ai
    assert "scripts/ai_check_pr.py" in makefile_ai
    assert 'scripts/ai_check_guards.py $(if $(CONTRACT),--contract $(CONTRACT))' in makefile_ai

    result = subprocess.run(
        ["make", "-n", "check-ai-pr", "AI_BASE_COMMIT=abc123"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'scripts/ai_check_pr.py --base "abc123"' in result.stdout


def test_upgrade_backs_up_policies_and_replaces_agent_marker_section(tmp_path):
    initial = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True,
    )
    assert initial.install() == 0
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8").replace("## AI Cockpit Rules", "## OLD RULES"), encoding="utf-8")
    checks = tmp_path / ".ai" / "cockpit" / "checks.yaml"
    checks.write_text("# LOCAL CUSTOM CHECKS\n", encoding="utf-8")
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        gitignore.read_text(encoding="utf-8")
        .replace(".ai/work-items/active/*.review.json\n", "")
        .replace(".ai/cockpit/upgrade-backups/\n", ""),
        encoding="utf-8",
    )

    upgrade = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True, upgrade=True,
    )
    assert upgrade.install() == 0

    upgraded_agents = agents.read_text(encoding="utf-8")
    assert "## OLD RULES" not in upgraded_agents
    assert "## AI Cockpit Rules" in upgraded_agents
    assert (tmp_path / ".ai" / "cockpit" / "version.json").is_file()
    backups = list((tmp_path / ".ai" / "cockpit" / "upgrade-backups").glob("*/.ai/cockpit/checks.yaml"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "# LOCAL CUSTOM CHECKS\n"
    upgraded_ignore = gitignore.read_text(encoding="utf-8")
    assert ".ai/work-items/active/*.review.json" in upgraded_ignore
    assert ".ai/cockpit/upgrade-backups/" in upgraded_ignore

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = subprocess.run(
        ["git", "check-ignore", ".ai/cockpit/upgrade-backups/example/checks.yaml"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.parametrize("name", ["AGENTS.md", "GEMINI.md", "CLAUDE.md"])
def test_upgrade_preserves_unmarked_agent_rules(tmp_path, name):
    custom_rules = "# Local Rules\n\nKEEP-ME\n"
    (tmp_path / name).write_text(custom_rules, encoding="utf-8")

    upgrade = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True, upgrade=True,
    )

    assert upgrade.install() == 0
    upgraded = (tmp_path / name).read_text(encoding="utf-8")
    assert upgraded.startswith(custom_rules)
    assert "KEEP-ME" in upgraded
    assert "<!-- AI_COCKPIT_SECTION -->" in upgraded
    assert "<!-- /AI_COCKPIT_SECTION -->" in upgraded


def test_commented_makefile_include_does_not_suppress_active_include(tmp_path):
    makefile = tmp_path / "Makefile"
    makefile.write_text("# include Makefile.ai\n", encoding="utf-8")
    installer = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True,
    )

    assert installer.install() == 0
    lines = makefile.read_text(encoding="utf-8").splitlines()
    assert "# include Makefile.ai" in lines
    assert "include Makefile.ai" in lines


def test_upgrade_refuses_active_work_item_before_writing(tmp_path):
    initial = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True,
    )
    assert initial.install() == 0
    checks = tmp_path / ".ai" / "cockpit" / "checks.yaml"
    checks.write_text("# KEEP\n", encoding="utf-8")
    active = tmp_path / ".ai" / "work-items" / "active" / "open.contract.json"
    active.write_text("{}\n", encoding="utf-8")

    upgrade = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True, upgrade=True,
    )

    assert upgrade.install() == 2
    assert checks.read_text(encoding="utf-8") == "# KEEP\n"
    assert not (tmp_path / ".ai" / "cockpit" / "upgrade-backups").exists()


def test_upgrade_with_active_requires_explicit_override(tmp_path):
    initial = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True,
    )
    assert initial.install() == 0
    active = tmp_path / ".ai" / "work-items" / "active" / "open.summary.json"
    active.write_text("{}\n", encoding="utf-8")

    upgrade = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True, upgrade=True, upgrade_with_active=True,
    )

    assert upgrade.install() == 0


def test_upgrade_rejects_distribution_downgrade_before_writing(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / ".ai" / "cockpit").mkdir(parents=True)
    (target / ".ai" / "cockpit").mkdir(parents=True)
    (source / ".ai" / "cockpit" / "version.json").write_text(
        json.dumps({"distributionVersion": 2, "contractSchema": 2}), encoding="utf-8"
    )
    target_version = target / ".ai" / "cockpit" / "version.json"
    target_version.write_text(
        json.dumps({"distributionVersion": 3, "contractSchema": 2}), encoding="utf-8"
    )

    upgrade = Installer(
        source=source, target=target, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=False, upgrade=True,
    )

    assert upgrade.install() == 2
    assert json.loads(target_version.read_text(encoding="utf-8"))["distributionVersion"] == 3
    assert not (target / ".ai" / "cockpit" / "upgrade-backups").exists()


def test_upgrade_rejects_malformed_source_version_before_writing(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / ".ai" / "cockpit").mkdir(parents=True)
    (source / ".ai" / "cockpit" / "version.json").write_text(
        '{"distributionVersion": "two"}', encoding="utf-8"
    )

    upgrade = Installer(
        source=source, target=target, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=False, upgrade=True,
    )

    assert upgrade.install() == 2
    assert not target.exists()


def test_upgrade_rolls_back_when_post_copy_validation_fails(tmp_path, monkeypatch):
    initial = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True,
    )
    assert initial.install() == 0
    checks = tmp_path / ".ai" / "cockpit" / "checks.yaml"
    checks.write_text("# CUSTOM BEFORE UPGRADE\n", encoding="utf-8")

    upgrade = Installer(
        source=ROOT, target=tmp_path, stack="generic", force=False, dry_run=False,
        with_examples=False, update_makefile=True, upgrade=True,
    )
    monkeypatch.setattr(
        upgrade,
        "validate_upgraded_installation",
        lambda: (_ for _ in ()).throw(ValueError("simulated validation failure")),
    )

    assert upgrade.install() == 2
    assert checks.read_text(encoding="utf-8") == "# CUSTOM BEFORE UPGRADE\n"
