from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_repository_and_installed_rules_share_outcome_terminality_boundary():
    for relative in ("AGENTS.md", "templates/agents/AI_COCKPIT_RULES.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "current Work Item" in text
        assert "Outcome: 🟢" in text
        assert "status=completed" in text
        assert "humanStatusColor=green" in text
        assert "new Work Item" in text


def test_rules_keep_successor_creation_narrow():
    for relative in ("AGENTS.md", "templates/agents/AI_COCKPIT_RULES.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "scope, authority, or base" in text
