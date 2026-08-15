"""Tests for the trilingual core-understanding P0 documentation journey."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = {"en": "", "ja": ".ja", "zh-CN": ".zh-CN"}
TOPICS = {
    "purpose": "docs/purpose{suffix}.md",
    "philosophy": "docs/philosophy/design-philosophy{suffix}.md",
    "architecture": "docs/architecture{suffix}.md",
    "capabilities": "docs/capabilities{suffix}.md",
}
REQUIRED_SECTIONS = (
    "Purpose",
    "Audience",
    "Outcome",
    "Scenario",
    "Explanation",
    "Action or decision",
    "Stop conditions",
    "Next steps",
    "Technical depth",
)


def links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def test_core_p0_pages_exist_with_the_same_reading_contract() -> None:
    for suffix in LOCALES.values():
        for template in TOPICS.values():
            path = ROOT / template.format(suffix=suffix)
            assert path.exists(), path
            text = path.read_text(encoding="utf-8")
            positions = [text.find(f"## {section}") for section in REQUIRED_SECTIONS]
            assert all(position >= 0 for position in positions), path
            assert positions == sorted(positions), path


def test_localized_core_pages_link_to_same_language_core_topics() -> None:
    for suffix in (".ja", ".zh-CN"):
        expected_suffix = f"{suffix}.md"
        for template in TOPICS.values():
            path = ROOT / template.format(suffix=suffix)
            text = path.read_text(encoding="utf-8")
            core_links = [target for target in links(text) if "docs/" in target]
            assert all(
                not target.endswith(".md")
                or target.endswith(expected_suffix)
                or "trust-layer" in target
                or "decision-states" in target
                or "capability-truth-matrix" in target
                for target in core_links
            ), (path, core_links)


def test_core_p0_pages_have_no_silent_entry_fallback() -> None:
    for suffix in (".ja", ".zh-CN"):
        for template in TOPICS.values():
            text = (ROOT / template.format(suffix=suffix)).read_text(encoding="utf-8")
            assert "silent fallback" not in text.lower(), template


def test_registry_promotes_only_the_four_migrated_core_topics() -> None:
    registry = json.loads(
        (ROOT / "docs/reference/documentation-authority-registry.json").read_text(encoding="utf-8")
    )
    topics = {topic["topic"]: topic for topic in registry["topics"]}
    for topic, template in {
        "project-purpose": TOPICS["purpose"],
        "design-philosophy": TOPICS["philosophy"],
        "project-architecture": TOPICS["architecture"],
        "capability-boundaries": TOPICS["capabilities"],
    }.items():
        record = topics[topic]
        assert record["enforcementStatus"] == "active"
        assert record["canonicalPath"] == template.format(suffix="")
        assert set(record["localizedPaths"]) == set(LOCALES)
        assert all((ROOT / path).exists() for path in record["localizedPaths"].values())

    assert topics["decision-states"]["enforcementStatus"] == "active"
    assert topics["lifecycle"]["enforcementStatus"] == "active"
    assert topics["recovery"]["enforcementStatus"] == "active"
    assert topics["first-calibration"]["enforcementStatus"] == "active"


def test_boundary_page_keeps_local_and_external_responsibilities_distinct() -> None:
    for suffix in LOCALES.values():
        text = (ROOT / TOPICS["capabilities"].format(suffix=suffix)).read_text(encoding="utf-8")
        lowered = text.lower()
        assert "repository governance layer" in lowered or "repository governance" in lowered
        assert "agent runtime" in lowered
        assert "security sandbox" in lowered
        assert "human" in lowered or "人" in lowered
