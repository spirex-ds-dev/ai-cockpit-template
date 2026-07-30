from pathlib import Path

from check_real_absurd_injection_docs import CASE_IDS, check_repository


ROOT = Path(__file__).resolve().parents[1]


def test_real_absurd_injection_documents_are_complete_and_aligned() -> None:
    assert check_repository(ROOT) == []


def test_real_absurd_injection_documents_define_all_twelve_case_ids() -> None:
    assert CASE_IDS == tuple(f"RAI-{number:02d}" for number in range(1, 13))


def test_real_absurd_injection_documents_require_an_actionable_refusal_record() -> None:
    expected_markers = {
        "docs/reference/real-absurd-injection-cases.md": (
            "Cannot continue",
            "Missing evidence",
            "Recovery condition",
        ),
        "docs/reference/real-absurd-injection-cases.zh-CN.md": (
            "不能继续",
            "缺失证据",
            "恢复条件",
        ),
        "docs/reference/real-absurd-injection-cases.ja.md": (
            "続行できません",
            "不足している証拠",
            "回復条件",
        ),
    }

    for relative_path, markers in expected_markers.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert all(marker in text for marker in markers)


def test_real_absurd_injection_documents_define_the_shared_traffic_lights() -> None:
    expected_markers = {
        "docs/reference/real-absurd-injection-cases.md": ("🟢 Allow", "🟡 Risk", "🔴 Block"),
        "docs/reference/real-absurd-injection-cases.zh-CN.md": (
            "🟢 允许",
            "🟡 风险",
            "🔴 阻止",
        ),
        "docs/reference/real-absurd-injection-cases.ja.md": (
            "🟢 許可",
            "🟡 リスク",
            "🔴 ブロック",
        ),
    }

    for relative_path, markers in expected_markers.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert all(marker in text for marker in markers)
