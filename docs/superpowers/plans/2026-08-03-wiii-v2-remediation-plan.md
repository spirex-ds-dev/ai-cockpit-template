---
author: Ray
title: "Work Item Intelligence V2 remediation implementation plan"
description: "Independently deliverable Work Items for correcting and scaling the local WIII interface."
status: current
---

# Work Item Intelligence V2 Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` for focused investigation and review, but execute the Work Item PR/archive/merge/closure lifecycles serially. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a correct, source-bound, scalable local WIII interface and evidence-based verification-cost improvements through independently closed Work Items.

**Architecture:** V2 separates authoritative governance projections from runtime observations, reduces current keyed entities rather than historical fact types, and publishes per-item snapshots/index entries. A cache is rebuildable and never authoritative. Lifecycle timing precedes receipt reuse and verification graph work.

**Tech Stack:** Python standard library, JSON Schema, repository Make targets, pytest, GitHub PR checks, AI Cockpit Contract/Summary/archive lifecycle.

## Global Constraints

- Every task starts from the then-current `origin/main` on a dedicated `codex/<work-item-id>` branch/worktree.
- Every task records the user's direct authorization as `rawUserRequest` and `rawRequestSource`; restricted paths require truthful `restrictedWriteApproval`.
- Every task executes `ai-start → ready preflight → ai-prepare-implementation → TDD → ai-finish/archive → check-ai-pr → push → PR → hosted checks → merge without provider branch deletion → ai-close-work-item`.
- Every successor Contract explicitly scopes its own `.ai/work-items/active/<work-item-id>.contract.json`, `.summary.json`, `.outcome.json`, `.outcome.md`, `.ai/work-items/starts/<work-item-id>.json`, `.ai/work-items/archive/**`, and `.ai/cockpit/current_status.md`, in addition to the task-specific files listed below.
- Only `ai-close-work-item` may remove that Work Item's exact local and remote branch after merged-PR Head-SHA verification. No release, tag, provider configuration, historical archive rewrite, or unrelated cleanup is authorized.
- Preserve repository-local/read-only query behavior. Do not add scheduler, retry, cancellation, workflow-engine, agent-manager, remote transport, or credential behavior.
- A performance claim requires a recorded workload, profile, environment, and at least 30 samples. Candidate budgets are not present guarantees.
- Do not start a later implementation Work Item until all declared predecessors are archived, merged, and closed on the current remote base.
- Each task's Contract acceptance includes its listed focused tests, the affected test suite, documentation metadata when docs change, all required governance checks, and `ai-finish`; no task treats a green subset as full lifecycle proof.

---

### Task 1: Source-bound facts and version counters (`wiii-source-bound-versioning`)

**Files:**

- Modify: `scripts/ai_work_item_intelligence.py`
- Modify: `scripts/ai_work_item_status.py`
- Modify: `.ai/schemas/work-item-intelligence-snapshot.schema.json`
- Modify: `tests/test_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence_integration.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** current V1 fact files and the remediation design.

**Produces:** `SourceRef`, `subject`, `versions`, source validation, and explicit V1/V2 CLI selection for later reducer and publication tasks.

- [ ] Write failing tests for an unchanged rebuild preserving versions, a governance-visible change incrementing only governance/source sequence, a runtime-only observation incrementing only runtime observation, and a missing/digest-mismatched source returning `inconsistent`.

```python
from hashlib import sha256

def test_v2_rebuild_preserves_versions_when_projection_is_unchanged(tmp_path: Path) -> None:
    receipt = tmp_path / "preflight.json"
    receipt.write_text('{"status":"ready"}', encoding="utf-8")
    append_fact(
        "item-one",
        "preflight_state",
        {
            "subject": {"kind": "preflight", "id": "current"},
            "state": "open",
            "sourceRef": {
                "kind": "preflight_receipt",
                "path": str(receipt),
                "digest": "sha256:" + sha256(receipt.read_bytes()).hexdigest(),
            },
        },
        root=tmp_path,
    )
    before = read_snapshot("item-one", schema_version=2, root=tmp_path)["versions"]
    rebuild("item-one", root=tmp_path)
    assert read_snapshot("item-one", schema_version=2, root=tmp_path)["versions"] == before
```

- [ ] Run the focused test and confirm it fails because V2 versions/source validation do not exist.

Run: `python -m pytest -q tests/test_work_item_intelligence.py -k 'versions or source'`

- [ ] Implement minimal typed source references, source digest validation, persisted counters, and an additive V2 serializer. Keep V1 response mode explicit and unchanged for valid V1 facts.

- [ ] Re-run focused and full WIII tests; add CLI tests for `--schema-version 1` and `--schema-version 2`.

- [ ] Complete the full Work Item lifecycle and record the merged closure receipt before Task 2.

### Task 2: Keyed open-entity reducer (`wiii-open-entity-reducer`)

**Files:**

- Modify: `scripts/ai_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** Task 1 `subject`, `sourceRef`, and V2 version contract.

**Produces:** reducer support for `open`, `resolved`, `satisfied`, and `superseded` facts keyed by entity identity.

- [ ] Write failing tests for a failed verification resolved by a pass, two decisions with one pending, a missing dependency later satisfied, and `closed` taking effect after all open entities resolve.

```python
def test_only_unresolved_decisions_block_governance(tmp_path: Path) -> None:
    request_decision("approve-a", root=tmp_path)
    request_decision("approve-b", root=tmp_path)
    record_decision("approve-a", root=tmp_path)
    assert read_snapshot("item-one", schema_version=2, root=tmp_path)["governance"]["state"] == "needs_human_confirmation"
```

- [ ] Run the focused tests and confirm historical-type reduction fails them.

Run: `python -m pytest -q tests/test_work_item_intelligence.py -k 'resolved or decision or dependency'`

- [ ] Implement the smallest keyed-entity state table and source-bound resolution relationship; reject cross-subject and missing resolution references.

- [ ] Run focused tests, all WIII tests, and complete the Task 2 lifecycle.

### Task 3: Governance/runtime and completion boundary (`wiii-governance-runtime-boundary`)

**Files:**

- Modify: `scripts/ai_work_item_intelligence.py`
- Modify: `scripts/ai_work_item_status.py`
- Modify: `.ai/schemas/work-item-intelligence-snapshot.schema.json`
- Modify: `tests/test_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence_integration.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** Task 2 keyed reducer.

**Produces:** `governance`, `runtimeObservation`, `completion`, and `governancePermissions` V2 fields.

- [ ] Write failing schema/API tests proving activity cannot mutate governance version/state and `governancePermissions` contains only allowed governance phases, never retry/cancel instructions.

- [ ] Write a failing test for five independent completion booleans: implementation, verification, review, integration, closure.

- [ ] Implement V2 grouping and completion derivation; maintain documented V1 compatibility adapter behavior.

- [ ] Run focused schema/CLI tests, full WIII tests, and close Task 3.

### Task 4: Reproducible performance characterization (`wiii-performance-characterization`)

**Files:**

- Create: `scripts/ai_work_item_intelligence_benchmark.py`
- Create: `tests/test_work_item_intelligence_benchmark.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`
- Create: `docs/reference/work-item-intelligence-performance-baseline.md`

**Consumes:** V2 query shape from Task 3.

**Produces:** a non-mutating, reproducible benchmark report with profile/environment/workload evidence.

- [ ] Write failing tests for benchmark report validation: at least 30 samples per case, explicit W/F/concurrency profile, cold/warm mode, Python/filesystem fields, p50/p95/p99, timeout count, lock wait, and bytes written.

- [ ] Run the focused test and confirm the harness does not exist.

Run: `python -m pytest -q tests/test_work_item_intelligence_benchmark.py`

- [ ] Implement a temporary-directory-only harness. It must never update repository runtime data or declare budgets by itself.

- [ ] Execute cases `W={1,100}`, `F={1,1000,2000}`, concurrency `{1,8,32,64}`, with 30 samples per declared profile; archive only the summarized report and environment metadata.

- [ ] Close Task 4. Do not set an enforcement threshold unless the measured report supports it.

### Task 5: Per-item publication and rebuildable cache (`wiii-index-fragment-concurrency`)

**Files:**

- Modify: `scripts/ai_work_item_intelligence.py`
- Modify: `scripts/ai_work_item_status.py`
- Modify: `tests/test_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence_integration.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** Task 1 versions and Task 4 benchmark protocol.

**Produces:** item-local `index-entry.json`, a rebuildable aggregate cache, and a monotonic list cursor.

- [ ] Write failing cross-item tests: 64 distinct Work Items publish concurrently without shared index lock timeout; a reader sees an old complete publication, new complete publication, or `inconsistent`, never an omitted delta.

- [ ] Inject failure after snapshot replace and after index-entry replace; assert cache rebuild discovers all valid entries.

- [ ] Implement per-item publication ids, cache invalidation/rebuild, and cursor persistence; remove the shared write lock from the per-item path.

- [ ] Run the Task 4 workload and compare throughput with serial baseline. Require zero lost entries and zero timeout at the adopted workload before closing.

- [ ] Run `python -m pytest -q tests/test_work_item_intelligence.py tests/test_work_item_intelligence_integration.py`, documentation metadata checks, every required Contract check, and `make ai-finish TASK=wiii-index-fragment-concurrency`; record the measured profile and closure evidence.

### Task 6: Linear fact reduction and crash recovery (`wiii-linear-reduction-and-recovery`)

**Files:**

- Modify: `scripts/ai_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence.py`
- Modify: `tests/test_work_item_intelligence_integration.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** Task 5 publication protocol.

**Produces:** set-based fact validation, sequence metadata, incremental reduction, audit rebuild, and safe stale-lock recovery.

- [ ] Write failing tests that reject a duplicate/digest/sequence violation, preserve valid entries after a malformed cache, and recover a crashed writer without removing a live lock.

- [ ] Add a failing scale test that compares 500 and 2,000 facts using the Task 4 profile; the report must show bounded non-quadratic growth rather than a timing assertion tied to one machine.

- [ ] Implement one-pass validation, metadata-backed append, incremental reducer state, full audit rebuild, and owner/lease or OS-lock recovery.

- [ ] Verify fault injection produces only complete old/new publications or explicit `inconsistent`, then close Task 6.

- [ ] Run `python -m pytest -q tests/test_work_item_intelligence.py tests/test_work_item_intelligence_integration.py`, the Task 4 characterization report validation, every required Contract check, and `make ai-finish TASK=wiii-linear-reduction-and-recovery`.

### Task 7: Lifecycle timing model (`work-item-lifecycle-timing`)

**Files:**

- Modify: `scripts/ai_observability.py`
- Modify: `scripts/ai_start.py`
- Modify: `scripts/ai_preflight_review.py`
- Modify: `scripts/ai_finish.py`
- Modify: `scripts/ai_archive_work_item.py`
- Modify: `scripts/ai_close_work_item.py`
- Create: `tests/test_work_item_lifecycle_timing.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** current lifecycle command boundaries; it is logically independent of Tasks 5 and 6, but its PR is intentionally delivered after them so its public WIII documentation update is reviewed against the finalized V2 storage contract.

**Produces:** source-bound phase timing for planning, preflight, implementation, verification, finish, provider wait, and closure.

- [ ] Write failing tests for phase start/end pairing, active compute vs provider/human wait, repeated execution count, cache outcome, and absence of a claim when evidence is unavailable.

- [ ] Implement only deterministic local timing capture; provider and human wait remain `unknown` unless an authoritative source supplies them.

- [ ] Run focused tests and complete the Task 7 lifecycle.

- [ ] Run `python -m pytest -q tests/test_work_item_lifecycle_timing.py tests/test_observability.py`, all required Contract checks, and `make ai-finish TASK=work-item-lifecycle-timing`.

### Task 8: Verification evidence reuse decision (`verification-evidence-reuse`)

**Files:**

- Modify: `scripts/ai_verification_context.py`
- Modify: `scripts/ai_verify.py`
- Modify: `tests/test_verification_evidence.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`
- Create or modify: `docs/reference/verification-evidence-reuse.md`

**Consumes:** Task 7 timing evidence and current verification receipts.

**Produces:** either a source-backed no-change decision or content-addressed receipt validity binding `baseCommit`, `headCommit`, changed-files, command, environment, toolchain, and policy digests.

- [ ] Write failing tests for a reusable receipt and one invalidation case per binding input.

- [ ] Run timing evidence analysis. If it does not show a material, safely reusable duplicate verification cost, document the evidence and finish with no production change.

- [ ] If warranted, implement receipt reuse only for unchanged bindings; a required check with any changed binding must execute normally.

- [ ] Close Task 8 with a truthful decision record.

- [ ] In both the reuse and no-change paths, run `python -m pytest -q tests/test_verification_evidence.py`, validate the archived timing evidence, execute all required Contract checks, and run `make ai-finish TASK=verification-evidence-reuse`.

### Task 9: Verification impact graph routing (`verification-impact-dag-routing`)

**Files:**

- Modify: `scripts/ai_verification_policy.py`
- Modify: `scripts/ai_verify.py`
- Modify: `Makefile`
- Create: `tests/test_verification_impact_graph.py`
- Modify: `docs/reference/work-item-intelligence-interface.md`

**Consumes:** Task 8 receipt validity policy.

**Produces:** declared required nodes, dependency edges, parallelizable groups, cached nodes, invalidated nodes, and Fast/Finish/Hosted proof layers.

- [ ] Write failing tests that reject a graph which omits a required final-proof node and that invalidate a cached node when its receipt binding changes.

- [ ] Implement a declarative graph evaluator only; it reports required/parallelizable/cached state and never schedules a Work Item or executes an agent action.

- [ ] Validate Light, Standard, Strict, and Release graphs against current required checks, then close Task 9.

- [ ] Run `python -m pytest -q tests/test_verification_impact_graph.py tests/test_verification_evidence.py`, all required Contract checks, and `make ai-finish TASK=verification-impact-dag-routing`. This task validates declared Release graph nodes only; it must not publish a release, alter provider configuration, or create tags.

### Task 10: V2 integration and truth audit (`wiii-v2-integration-and-truth-audit`)

**Files:**

- Create: `docs/reference/wiii-v2-integration-audit.md`
- Modify: `tests/test_work_item_intelligence_integration.py`

**Consumes:** every closed predecessor Work Item.

**Produces:** final V1/V2 compatibility decision, installer/reference parity evidence, documented limits, and end-to-end lifecycle proof.

- [ ] Write failing integration tests for V1 explicit mode, V2 explicit mode, inconsistent source behavior, multi-item publication/rebuild, and no scheduler/network side effect.

- [ ] Run all focused WIII, lifecycle, verification, documentation, multilingual, and installer checks declared by the Contract.

- [ ] Review every capability claim against current evidence. Record unsupported claims as findings; do not modify capability/multilingual truth documents, production code, or schemas in this audit Work Item and do not use the original assessment scores as facts.

- [ ] Run the listed integration suite, documentation metadata checks, all required Contract checks, and `make ai-finish TASK=wiii-v2-integration-and-truth-audit`; complete the final PR and `ai-close-work-item`.

### Task 11: Bounded truth-alignment corrective (`wiii-v2-truth-alignment-corrective`)

**Files:**

- Modify: `docs/reference/work-item-intelligence-interface.md`
- Modify: `docs/reference/capability-truth-matrix.json`
- Modify: `docs/reference/capability-truth-matrix.md`
- Modify: `docs/reference/documentation-context-registry.json`
- Modify: `docs/reference/japanese-capability-assessment.json`
- Modify: `docs/reference/japanese-capability-assessment.md`
- Modify: `tests/test_work_item_intelligence_integration.py`

**Consumes:** Task 10 audit findings. This task starts only if Task 10 identifies a documented claim that differs from verified current behavior; otherwise it is recorded as `not_required` in Task 10's Summary and is not started.

**Produces:** a narrowly evidenced correction of published WIII truth. It may not change product behavior, provider configuration, releases, tags, or archives.

- [ ] For every Task 10 finding, write a failing claim-parity test that names the precise current behavior and affected document field.

- [ ] Update only the named documentation/registry/multilingual truth records, run the focused integration and documentation checks, all required Contract checks, and `make ai-finish TASK=wiii-v2-truth-alignment-corrective`.

## Execution schedule

Only research, test design, and review may run in parallel. Merge/closure order is:

1. Tasks 1–3 serially.
2. Task 4 characterization.
3. Tasks 5–6 serially.
4. Task 7.
5. Tasks 8–9 serially when Task 7 evidence supports them.
6. Task 10 final audit.
7. Task 11 only when Task 10 records an actual truth-drift finding.

For each task, use a fresh sub-agent for scoped investigation/implementation review and a second scoped reviewer before `ai-finish`. The controller independently verifies the diff and commands, then serializes push, PR, merge, and closure. This preserves the requested multi-agent workflow without overlapping archive/index ownership.
