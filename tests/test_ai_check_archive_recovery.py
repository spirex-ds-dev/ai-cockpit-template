import ai_check_archive_recovery


def test_recovery_rejects_archive_sequence_already_owned_by_target_base():
    errors = ai_check_archive_recovery.recovery_collisions(
        {"entries": [{"contractPath": "archive/rfe-104.contract.json", "archiveSequence": 666}]},
        {"entries": [{"contractPath": "archive/rfe-106.contract.json", "archiveSequence": 666}]},
        {"instructions": []},
        {"instructions": []},
    )
    assert errors == [
        "archive sequence 666 is already owned on the target base by archive/rfe-106.contract.json; do not rebase archived evidence, create a successor Work Item"
    ]


def test_recovery_rejects_traceability_id_already_owned_by_target_base():
    errors = ai_check_archive_recovery.recovery_collisions(
        {"entries": []},
        {"entries": []},
        {
            "instructions": [
                {"id": "PLAN-DIRECTIVE-049", "contractPaths": ["archive/rfe-104.contract.json"]}
            ]
        },
        {
            "instructions": [
                {"id": "PLAN-DIRECTIVE-049", "contractPaths": ["archive/rfe-106.contract.json"]}
            ]
        },
    )
    assert errors == [
        "traceability id PLAN-DIRECTIVE-049 is already owned on the target base by archive/rfe-106.contract.json; do not overwrite or renumber archived evidence, create a successor Work Item"
    ]


def test_recovery_accepts_unique_records():
    assert (
        ai_check_archive_recovery.recovery_collisions(
            {
                "entries": [
                    {"contractPath": "archive/rfe-104.contract.json", "archiveSequence": 667}
                ]
            },
            {
                "entries": [
                    {"contractPath": "archive/rfe-106.contract.json", "archiveSequence": 666}
                ]
            },
            {
                "instructions": [
                    {"id": "PLAN-DIRECTIVE-050", "contractPaths": ["archive/rfe-104.contract.json"]}
                ]
            },
            {
                "instructions": [
                    {"id": "PLAN-DIRECTIVE-049", "contractPaths": ["archive/rfe-106.contract.json"]}
                ]
            },
        )
        == []
    )
