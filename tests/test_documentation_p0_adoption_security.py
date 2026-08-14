"""Structural checks for the P0 adoption and security reader journey."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
LOCALES = {"en": "", "ja": ".ja", "zh-CN": ".zh-CN"}


def _read(path: str, locale: str = "") -> str:
    return (ROOT / f"{path}{locale}.md").read_text(encoding="utf-8")


def test_p0_adoption_topics_have_all_locale_siblings_and_same_language_routes():
    topics = {
        "installation": "docs/getting-started/installation",
        "first-calibration": "docs/getting-started/first-calibration",
        "first-work-item": "docs/getting-started/first-work-item",
    }
    for path in topics.values():
        for locale in LOCALES.values():
            assert (ROOT / f"{path}{locale}.md").exists(), path + locale
    for locale in LOCALES.values():
        installation = _read("docs/getting-started/installation", locale)
        calibration = _read("docs/getting-started/first-calibration", locale)
        work_item = _read("docs/getting-started/first-work-item", locale)
        assert "first-calibration" in installation
        assert "first-work-item" in calibration
        assert "fallback" not in installation.lower() + calibration.lower() + work_item.lower()


def test_security_boundary_has_localized_semantics_and_external_owner():
    for locale in LOCALES.values():
        text = _read("docs/security/injection-boundary", locale).lower()
        assert "untrusted" in text or "不可信" in text or "信頼" in text
        assert "external" in text or "外部" in text
        assert "sandbox" in text or "沙箱" in text
        assert not any(
            claim in text
            for claim in ("is a security sandbox", "是安全沙箱", "security sandbox です")
        )


def test_registry_activates_only_complete_p0_topics():
    registry = json.loads(
        (ROOT / "docs/reference/documentation-authority-registry.json").read_text()
    )
    topics = {item["topic"]: item for item in registry["topics"]}
    for topic in ("installation", "first-calibration", "first-work-item", "security-boundaries"):
        item = topics[topic]
        assert item["enforcementStatus"] == "active"
        for path in item["localizedPaths"].values():
            assert (ROOT / path).exists(), path
        assert item["plainLanguageRequired"] is True


def test_localized_homes_expose_adoption_and_security_routes_without_fallback():
    for locale in LOCALES.values():
        text = (ROOT / f"docs/README{locale}.md").read_text(encoding="utf-8").lower()
        assert "first-calibration" in text or "首次校准" in text or "最初の calibration" in text
        assert "injection-boundary" in text or "注入边界" in text or "injection boundary" in text
        adoption_slice = (
            text.split("## 按读者目标选择", 1)[-1] if "## 按读者目标选择" in text else text
        )
        assert "fallback" not in adoption_slice
