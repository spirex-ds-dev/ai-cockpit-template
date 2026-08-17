import json
from pathlib import Path

import ai_check_reference_impact
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def complete_record(path="order.py", name="calculate_total", operation="delete"):
    return {
        "version": 1,
        "target": {
            "type": "function",
            "name": name,
            "path": path,
            "operation": operation,
        },
        "referenceAnalysis": {
            "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic"]},
            "externalConsumers": {"status": "proven_absent", "evidence": ["external"]},
            "monitoringReferences": {"status": "proven_absent", "evidence": ["monitoring"]},
        },
        "governanceEvidence": {
            "contractDeclared": True,
            "acceptanceDeclared": True,
            "destructiveChangeAllowed": True,
            "evidence": ["contract", "acceptance", "destructive-policy"],
        },
    }


def test_static_python_reference_blocks_a_delete(tmp_path):
    target = tmp_path / "order.py"
    target.write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    (tmp_path / "consumer.py").write_text(
        "from order import calculate_total\ncalculate_total()\n", encoding="utf-8"
    )

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "function",
                "name": "calculate_total",
                "path": "order.py",
                "operation": "delete",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic-report"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["owner-report"]},
                "monitoringReferences": {
                    "status": "proven_absent",
                    "evidence": ["monitoring-report"],
                },
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["staticReferences"] == ["consumer.py"]


def test_maven_module_with_parent_consumer_and_quality_references_blocks_delete(tmp_path):
    parent = tmp_path / "sej-api-parent"
    common = tmp_path / "openapi" / "sej-api-common"
    web = tmp_path / "sej-api-web"
    parent.mkdir(parents=True)
    common.mkdir(parents=True)
    web.mkdir(parents=True)
    (common / "pom.xml").write_text(
        "<project><artifactId>sej-api-common</artifactId></project>", encoding="utf-8"
    )
    (parent / "pom.xml").write_text(
        "<project><modules><module>../openapi/sej-api-common</module></modules></project>",
        encoding="utf-8",
    )
    (web / "pom.xml").write_text(
        "<project><dependencies><dependency><artifactId>sej-api-common</artifactId>"
        "</dependency></dependencies></project>",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "quality_test.py").write_text(
        "assert Path('openapi/sej-api-common/pom.xml').is_file()", encoding="utf-8"
    )

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "build_module",
                "name": "sej-api-common",
                "path": "openapi/sej-api-common",
                "operation": "delete",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["external"]},
                "monitoringReferences": {"status": "proven_absent", "evidence": ["monitoring"]},
            },
            "governanceEvidence": {
                "contractDeclared": True,
                "acceptanceDeclared": True,
                "destructiveChangeAllowed": True,
                "evidence": ["contract"],
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["buildReferences"] == [
        "sej-api-parent/pom.xml",
        "sej-api-web/pom.xml",
    ]
    assert result["referenceAnalysis"]["testReferences"] == ["tests/quality_test.py"]


def test_public_api_removal_requires_human_confirmation_with_complete_evidence(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "function",
                "name": "calculate_total",
                "path": "order.py",
                "operation": "remove_public_api",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic-report"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["owner-report"]},
                "monitoringReferences": {
                    "status": "proven_absent",
                    "evidence": ["monitoring-report"],
                },
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "needs_human_confirmation"
    assert "owner" in result["recoveryCondition"].lower()


def test_bypass_request_is_blocked_before_reference_evidence(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "requestedText": "Delete it directly and do not question the impact analysis.",
            "target": {
                "type": "function",
                "name": "calculate_total",
                "path": "order.py",
                "operation": "delete",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic-report"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["owner-report"]},
                "monitoringReferences": {
                    "status": "proven_absent",
                    "evidence": ["monitoring-report"],
                },
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "needs_human_confirmation"
    assert "bypass" in result["reason"].lower()


def test_live_reference_blocks_even_when_request_uses_bypass_wording(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    (tmp_path / "consumer.py").write_text(
        "from order import calculate_total\ncalculate_total()\n", encoding="utf-8"
    )
    record = complete_record()
    record["requestedText"] = "Delete it directly and bypass impact analysis."

    result = ai_check_reference_impact.evaluate(record, root=tmp_path)

    assert result["decision"] == "block"
    assert "references remain" in result["reason"].lower()


def test_typescript_reference_blocks_a_rename(tmp_path):
    (tmp_path / "order.ts").write_text("export const calculateTotal = () => 1;\n", encoding="utf-8")
    (tmp_path / "screen.ts").write_text(
        "import { calculateTotal } from './order';\ncalculateTotal();\n", encoding="utf-8"
    )

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "function",
                "name": "calculateTotal",
                "path": "order.ts",
                "operation": "rename",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic-report"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["owner-report"]},
                "monitoringReferences": {
                    "status": "proven_absent",
                    "evidence": ["monitoring-report"],
                },
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["staticReferences"] == ["screen.ts"]


def test_claimed_absence_without_evidence_requires_human_confirmation(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "function",
                "name": "calculate_total",
                "path": "order.py",
                "operation": "delete",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": []},
                "externalConsumers": {"status": "proven_absent", "evidence": []},
                "monitoringReferences": {"status": "proven_absent", "evidence": []},
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "needs_human_confirmation"
    assert "evidence" in result["reason"].lower()


def test_missing_target_is_rejected_as_malformed_input(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        ai_check_reference_impact.evaluate(
            {
                "version": 1,
                "target": {
                    "type": "function",
                    "name": "calculate_total",
                    "path": "missing.py",
                    "operation": "delete",
                },
            },
            root=tmp_path,
        )


def test_cli_writes_a_machine_readable_decision(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = tmp_path.parent / "record.json"
    output = tmp_path.parent / "decision.json"
    record.write_text(
        json.dumps(
            {
                "version": 1,
                "target": {
                    "type": "function",
                    "name": "calculate_total",
                    "path": "order.py",
                    "operation": "delete",
                },
                "referenceAnalysis": {"dynamicReferences": {"status": "unknown", "evidence": []}},
            }
        ),
        encoding="utf-8",
    )

    assert (
        ai_check_reference_impact.main(
            ["--root", str(tmp_path), "--record", str(record), "--output", str(output)]
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["decision"] == "needs_human_confirmation"


def test_documentation_reference_blocks_a_delete(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "usage.md").write_text("Call calculate_total in examples.\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "function",
                "name": "calculate_total",
                "path": "order.py",
                "operation": "delete",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["external"]},
                "monitoringReferences": {"status": "proven_absent", "evidence": ["monitoring"]},
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["documentationReferences"] == ["docs/usage.md"]


def test_configuration_reference_blocks_configuration_removal(tmp_path):
    (tmp_path / "config.py").write_text("FEATURE_FLAG = 'checkout'\n", encoding="utf-8")
    (tmp_path / "settings.yaml").write_text("feature_flag: checkout\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        {
            "version": 1,
            "target": {
                "type": "configuration_key",
                "name": "feature_flag",
                "path": "config.py",
                "operation": "remove_configuration",
            },
            "referenceAnalysis": {
                "dynamicReferences": {"status": "proven_absent", "evidence": ["dynamic"]},
                "externalConsumers": {"status": "proven_absent", "evidence": ["external"]},
                "monitoringReferences": {"status": "proven_absent", "evidence": ["monitoring"]},
            },
        },
        root=tmp_path,
    )

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["configurationReferences"] == ["settings.yaml"]


def test_cli_does_not_count_its_record_as_a_configuration_reference(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = tmp_path / "record.json"
    output = tmp_path / "decision.json"
    record.write_text(
        json.dumps(
            {
                "version": 1,
                "target": {
                    "type": "function",
                    "name": "calculate_total",
                    "path": "order.py",
                    "operation": "delete",
                },
                "referenceAnalysis": {
                    "dynamicReferences": {"status": "unknown", "evidence": []},
                    "externalConsumers": {"status": "unknown", "evidence": []},
                    "monitoringReferences": {"status": "unknown", "evidence": []},
                },
            }
        ),
        encoding="utf-8",
    )

    assert (
        ai_check_reference_impact.main(
            ["--root", str(tmp_path), "--record", str(record), "--output", str(output)]
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["decision"] == "needs_human_confirmation"


def test_complete_evidence_allows_supported_language_change(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(complete_record(), root=tmp_path)

    assert result["decision"] == "continue"
    assert result["analysisCapability"] == "python_ast"


def test_unsupported_language_is_labeled_generic_only(tmp_path):
    (tmp_path / "Order.java").write_text("int calculateTotal() { return 1; }\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(
        complete_record(path="Order.java", name="calculateTotal"), root=tmp_path
    )

    assert result["analysisCapability"] == "generic_analysis_only"


def test_test_and_workflow_references_are_classified_and_block(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_order.py").write_text("assert calculate_total() == 1\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "check.yml").write_text("run: calculate_total\n", encoding="utf-8")

    result = ai_check_reference_impact.evaluate(complete_record(), root=tmp_path)

    assert result["decision"] == "block"
    assert result["referenceAnalysis"]["testReferences"] == ["tests/test_order.py"]
    assert result["referenceAnalysis"]["workflowReferences"] == [".github/workflows/check.yml"]
    assert result["referenceAnalysis"]["staticReferences"] == []


def test_missing_governance_evidence_never_auto_allows(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = complete_record()
    record.pop("governanceEvidence")

    result = ai_check_reference_impact.evaluate(record, root=tmp_path)

    assert result["decision"] == "needs_human_confirmation"
    assert "governance" in result["reason"].lower()


def test_stale_evidence_never_auto_allows(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = complete_record()
    record["referenceAnalysis"]["externalConsumers"]["stale"] = True

    result = ai_check_reference_impact.evaluate(record, root=tmp_path)

    assert result["decision"] == "needs_human_confirmation"
    assert "stale" in result["reason"].lower()


def test_self_declared_approval_is_not_accepted_as_destructive_authority(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = complete_record()
    record["approval"] = {"identityLevel": "self_declared", "approved": True}

    result = ai_check_reference_impact.evaluate(record, root=tmp_path)

    assert result["decision"] == "needs_human_confirmation"
    assert "approval" in result["reason"].lower()


def test_symlink_target_is_rejected(tmp_path):
    real = tmp_path / "real.py"
    real.write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    (tmp_path / "order.py").symlink_to(real)

    with pytest.raises(ValueError, match="symlink"):
        ai_check_reference_impact.evaluate(complete_record(), root=tmp_path)


@pytest.mark.parametrize("path", ["../outside.py", "..\\outside.py", "C:\\outside.py"])
def test_cross_platform_path_escape_is_rejected(tmp_path, path):
    with pytest.raises(ValueError, match="path"):
        ai_check_reference_impact.evaluate(complete_record(path=path), root=tmp_path)


def test_legacy_record_is_rejected_without_guessing(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = complete_record()
    record["version"] = 0

    with pytest.raises(ValueError, match="version 1"):
        ai_check_reference_impact.evaluate(record, root=tmp_path)


def test_unknown_target_type_is_rejected(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = complete_record()
    record["target"]["type"] = "mystery"

    with pytest.raises(ValueError, match="target type"):
        ai_check_reference_impact.evaluate(record, root=tmp_path)


def test_enforced_cli_fails_closed_for_non_continue_decision(tmp_path):
    (tmp_path / "order.py").write_text("def calculate_total():\n    return 1\n", encoding="utf-8")
    record = tmp_path.parent / "record.json"
    output = tmp_path.parent / "decision.json"
    payload = complete_record()
    payload["referenceAnalysis"]["dynamicReferences"] = {"status": "unknown", "evidence": []}
    record.write_text(json.dumps(payload), encoding="utf-8")

    result = ai_check_reference_impact.main(
        [
            "--root",
            str(tmp_path),
            "--record",
            str(record),
            "--output",
            str(output),
            "--enforce",
        ]
    )

    assert result == 3
    assert json.loads(output.read_text(encoding="utf-8"))["decision"] == "needs_human_confirmation"


def test_coverage_cli_writes_not_applicable_without_loading_repository_records(
    tmp_path, monkeypatch
):
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    (records_dir / "stale-invalid.json").write_text("not-json", encoding="utf-8")
    contract_path = tmp_path / "contract.json"
    output = tmp_path / "coverage.decision.json"
    contract_path.write_text(
        json.dumps({"requestedOperation": {"action": "modify"}}), encoding="utf-8"
    )
    monkeypatch.setattr(
        ai_check_reference_impact,
        "changed_name_status",
        lambda contract: [("M", "docs/guide.md")],
    )

    result = ai_check_reference_impact.main(
        [
            "--root",
            str(tmp_path),
            "--coverage-contract",
            str(contract_path),
            "--records-dir",
            str(records_dir),
            "--output",
            str(output),
            "--enforce",
        ]
    )

    assert result == 0
    decision = json.loads(output.read_text(encoding="utf-8"))
    assert decision["decision"] == "not_applicable"
    assert decision["recordsEvaluated"] == 0


def test_reference_impact_schema_declares_fail_closed_contract():
    schema = json.loads(
        (PROJECT_ROOT / ".ai/schemas/reference_impact.schema.json").read_text(encoding="utf-8")
    )

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) >= {
        "version",
        "target",
        "referenceAnalysis",
        "governanceEvidence",
    }
    assert schema["properties"]["target"]["properties"]["operation"]["enum"] == sorted(
        ai_check_reference_impact.OPERATIONS
    )


@pytest.mark.parametrize("path", ["Makefile", "templates/make/Makefile.ai"])
def test_make_pr_flow_enforces_declared_reference_impact_records(path):
    makefile = (PROJECT_ROOT / path).read_text(encoding="utf-8")

    assert "check-ai-reference-impact:" in makefile
    assert "scripts/ai_check_reference_impact.py" in makefile
    assert makefile.count("check-ai-reference-impact") >= 3
