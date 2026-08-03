import ai_verification_policy


def test_graph_rejects_missing_required_final_proof_node():
    graph = {
        "nodes": {
            "fast": {"layer": "Fast", "required": True, "dependsOn": []},
            "finish": {"layer": "Finish", "required": True, "dependsOn": ["fast"]},
        }
    }

    result = ai_verification_policy.evaluate_impact_graph(
        graph, profile="standard", receipt_bindings={}
    )

    assert result["valid"] is False
    assert result["errors"] == ["required final proof node is missing"]


def test_graph_invalidates_cached_node_when_receipt_binding_changes():
    graph = {
        "nodes": {
            "fast": {
                "layer": "Fast",
                "required": True,
                "dependsOn": [],
                "receiptBindings": {
                    "baseCommit": "a",
                    "headCommit": "b",
                    "changedPaths": "c",
                    "command": "d",
                    "environment": "e",
                    "toolchain": "f",
                    "policy": "g",
                },
            },
            "finish": {"layer": "Finish", "required": True, "dependsOn": ["fast"]},
            "hosted": {
                "layer": "Hosted",
                "required": True,
                "finalProof": True,
                "dependsOn": ["finish"],
            },
        }
    }

    result = ai_verification_policy.evaluate_impact_graph(
        graph,
        profile="standard",
        receipt_bindings={
            "baseCommit": "changed",
            "headCommit": "b",
            "changedPaths": "c",
            "command": "d",
            "environment": "e",
            "toolchain": "f",
            "policy": "g",
        },
    )

    assert result["cachedNodes"] == []
    assert result["invalidatedNodes"] == ["fast"]


def test_default_graph_exposes_fast_finish_and_hosted_proof_layers():
    result = ai_verification_policy.evaluate_current_impact_graph(
        profile="release", receipt_bindings={}
    )

    assert result["valid"] is True
    assert result["proofLayers"] == {"Fast": ["fast"], "Finish": ["finish"], "Hosted": ["hosted"]}
