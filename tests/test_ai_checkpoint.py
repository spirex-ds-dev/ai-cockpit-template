import ai_checkpoint


def test_intent_context_defaults_when_intent_is_missing():
    assert ai_checkpoint.intent_context({"workItemId": "task"}) == [
        "problem: not provided",
        "constraint: not provided",
        "rationale: not provided",
    ]


def test_intent_context_keeps_values_and_default_placeholders():
    assert ai_checkpoint.intent_context(
        {
            "intent": {
                "problem": "Resolve optional intent compatibility.",
                "constraints": ["Keep V2 backward compatible."],
            }
        }
    ) == [
        "problem: Resolve optional intent compatibility.",
        "constraint: Keep V2 backward compatible.",
        "rationale: not provided",
    ]
