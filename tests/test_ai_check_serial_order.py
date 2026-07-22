import ai_check_serial_order


def test_incomplete_predecessor_is_blocked():
    issues = ai_check_serial_order.validate_predecessor(
        {
            "workItemId": "previous",
            "status": "archived",
            "pr": {"merged": True},
            "closure": {
                "succeeded": False,
                "localBranchDeleted": False,
                "remoteBranchDeleted": False,
                "baseSynchronized": False,
            },
        }
    )
    assert "closure.succeeded must be true" in issues
    assert "closure.remoteBranchDeleted must be true" in issues


def test_complete_predecessor_is_allowed():
    assert (
        ai_check_serial_order.validate_predecessor(
            {
                "workItemId": "previous",
                "status": "closed",
                "pr": {"merged": True},
                "closure": {
                    "succeeded": True,
                    "localBranchDeleted": True,
                    "remoteBranchDeleted": True,
                    "baseSynchronized": True,
                },
            }
        )
        == []
    )
