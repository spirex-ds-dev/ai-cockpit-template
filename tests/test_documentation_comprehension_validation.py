import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PROTOCOLS = [
    ROOT / "docs/reference/comprehension-validation-protocol.md",
    ROOT / "docs/reference/comprehension-validation-protocol.zh-CN.md",
    ROOT / "docs/reference/comprehension-validation-protocol.ja.md",
]


def test_protocols_define_six_questions_and_no_comprehension_claim():
    for path in PROTOCOLS:
        text = path.read_text(encoding="utf-8")
        assert "comprehension_unverified" in text
        assert "1." in text and "6." in text
        assert any(term in text for term in ("not", "不是", "不证明", "証拠ではありません"))


def test_response_schema_is_anonymous_and_requires_six_answers():
    schema = json.loads(
        (ROOT / "docs/reference/comprehension-validation-response.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["additionalProperties"] is False
    assert schema["properties"]["consentConfirmed"]["const"] is True
    assert schema["properties"]["answers"]["minItems"] == 6
    assert schema["properties"]["answers"]["maxItems"] == 6
    assert schema["properties"]["identifyingData"]["const"] is None
