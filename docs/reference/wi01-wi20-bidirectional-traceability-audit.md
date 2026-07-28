---
author: Ray
title: "WI-01 through WI-20 Bidirectional Traceability Audit"
description: Human-readable view of the instruction, plan, implementation, acceptance, and corrective evidence audit.
keywords:
  - traceability
  - work-items
  - audit
  - acceptance
  - governance
---

# WI-01 through WI-20 Bidirectional Traceability Audit

## Result

The audit is complete. All twenty rows have instruction, plan, archived
Contract/Summary/Manifest, implementation or explicit no-change, acceptance, and
verification evidence. The executable checker validates the mapping in both
directions.

WI-10 originally had four release-blocking omissions. They were corrected by
`wi10-prompt-first-multiplatform-installation-20260728`, delivered through PR
#423, merged, closed, and reverified. No audit finding remains open.

WI-18 and WI-19 are intentionally deferred. Their historical evidence and
controls are valid, but publishing the new current version and cleaning the
current execution-plan documents remain later stages in the approved serial
order. Deferred does not mean missing evidence and does not authorize either
operation early.

The machine-readable authority for this report is
[`wi01-wi20-bidirectional-traceability-audit.json`](wi01-wi20-bidirectional-traceability-audit.json).

## Twenty-row evidence view

| Work Item | Audit state | Representative implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| WI-01 | verified | `.ai/schemas/canonical_evidence.schema.json`; `scripts/ai_canonical_evidence.py` | `tests/test_canonical_evidence.py` |
| WI-02 | verified | `.ai/schemas/unknown_assessment.schema.json`; `scripts/ai_unknown_confirmation.py` | `tests/test_unknown_confirmation.py` |
| WI-03 | verified | `scripts/ai_installer_transaction.py`; `scripts/install_ai_cockpit.py` | `tests/test_installer_transaction.py` |
| WI-04 | verified | `scripts/ai_calibration_inventory.py`; `docs/reference/calibration-inventory.md` | `tests/test_calibration_inventory.py` |
| WI-05 | verified | `scripts/ai_input_trust.py`; `docs/security-boundaries.md` | `tests/test_input_trust.py`; `tests/test_input_trust_corpus.py` |
| WI-06 | verified | `scripts/ai_capability_truth.py`; `docs/reference/capability-truth-matrix.json` | `tests/test_absurd_capability_truth.py`; `tests/test_capability_truth_matrix.py` |
| WI-07 | verified | `scripts/ai_work_item_state.py`; `docs/reference/work-item-state-machine.md` | `tests/test_work_item_state_machine.py` |
| WI-08 | verified | `scripts/ai_verification_policy.py`; `docs/reference/lightweight-verification-and-soft-gates.md` | `tests/test_verification_policy.py` |
| WI-09 | verified | `scripts/ai_check_task_outcome.py` | `tests/test_task_outcome_validator.py` |
| WI-10 | verified after corrective | Complete English, Chinese, and Japanese installation guides plus nine iOS, Android, and Java examples | `tests/test_docs_metadata.py` |
| WI-11 | verified | `docs/reference/enterprise-control-matrix.json`; `docs/enterprise-security-boundary.md` | `tests/test_enterprise_control_matrix.py` |
| WI-12 | verified | `scripts/ai_quality_architecture.py`; `docs/reference/test-architecture.md` | `tests/test_quality_architecture.py` |
| WI-13 | verified | `docs/reference/deprecated-assets-registry.json`; `scripts/check_deprecated_assets.py` | `tests/test_deprecated_assets.py` |
| WI-14 | verified | `scripts/ai_governance_compression.py`; `docs/reference/how-to-read-cockpit-status.ja.md` | `tests/test_governance_compression.py` |
| WI-15 | verified | `docs/reference/full-remediation-acceptance.md` | Archived `full-remediation-acceptance` Summary |
| WI-16 | verified | `scripts/ai_japanese_capability.py`; `docs/reference/japanese-capability-assessment.md` | `tests/test_japanese_capability.py` |
| WI-17 | verified | Complete English, Chinese, and Japanese Trust Layer documents | `tests/test_trust_layer_docs.py` |
| WI-18 | deferred by serial order | Release authority and capability mappings | `tests/test_trust_guards.py` |
| WI-19 | deferred by serial order | `docs/superpowers/plans/README.md` | `tests/test_plan_cleanup.sh` |
| WI-20 | verified | `scripts/run_quality_gate.py`; `.github/workflows/smoke.yml`; Japanese quality-gate operations guide | `tests/test_quality_telemetry.py`; `tests/test_ci_quality_orchestration.py` |

Every row's exact plan locator, archive triple, full implementation and
acceptance path list, reverse references, verification command, named-path
disposition, and finding IDs are recorded in the machine-readable authority.

## WI-10 corrective closure

The corrective archive triple is:

- `.ai/work-items/archive/2026/wi10-prompt-first-multiplatform-installation-20260728.contract.json`
- `.ai/work-items/archive/2026/wi10-prompt-first-multiplatform-installation-20260728.summary.json`
- `.ai/work-items/archive/2026/wi10-prompt-first-multiplatform-installation-20260728.archive-manifest.json`

It resolves:

- `WI10-AUDIT-001`: complete Chinese installation route;
- `WI10-AUDIT-002`: prompt-first primary path and explained retained commands;
- `WI10-AUDIT-003`: trilingual iOS, Android, and Java examples;
- `WI10-AUDIT-004`: complete zero-programming-experience wizard, scaffold,
  calibration, first Work Item, PR/CI, closure, success, and recovery hand
  sequence.

The traceability checker now requires every resolved corrective finding to bind
an exact archive triple from the canonical archive index. A resolved label by
itself cannot close a finding.

## Boundaries

Archived implementation evidence proves repository history and current
repository artifacts. It does not prove that an adopter has installed a
toolchain, that hosted controls are configured in another repository, that a
provider release has been published, or that enterprise compliance is
guaranteed.

WI-16 evidence proves deterministic Japanese governance-path coverage, not
unbounded native-level language fluency. The approved execution order still
requires a new comprehensive Japanese assessment immediately before
documentation alignment and release.

## Verification

Run:

```text
.venv/bin/python -m pytest -q tests/test_instruction_traceability.py
make check-instruction-traceability
```

The checker rejects missing or unknown WI IDs, missing evidence paths, archive
triple or digest drift, missing reverse references, unsupported named paths,
duplicate evidence ownership without a shared reason, resolved corrective
findings without indexed archive evidence, and a complete audit with an open
finding or incomplete row.
