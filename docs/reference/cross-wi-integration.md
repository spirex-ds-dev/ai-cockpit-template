---
author: Ray
title: Cross-WI Integration Report
description: Deterministic final acceptance of the WI-04 through WI-13 evidence chain.
---

# Cross-WI Integration Report

WI-14 reads the immutable archive bundles for WI-04 through WI-13 and emits a
single advisory report. It does not rewrite historical evidence, change gates,
or make runtime decisions.

## Command

```sh
python scripts/ai_cross_wi_integration.py \
  --root . \
  --output target/cross-wi-integration.json \
  --markdown target/cross-wi-integration.md
```

The JSON source digest is computed from sorted archive paths and bytes. The
same inputs therefore produce the same report; wall-clock timestamps are not
part of the fact source.

## Per-WI acceptance

Each row requires the exact successor/archive identity and validates Contract,
Summary, Outcome, Outcome Markdown, archive manifest paths, and SHA-256
bindings. A missing, malformed, cross-task, or digest-mismatched artifact is a
red fail-closed result. `completed` maps to green and
`completed_with_warnings` maps to yellow; warnings and limitations remain
visible instead of being promoted to a pass. The `outcomeSections` object keeps
all Outcome sections—delivered changes, findings, risks, warnings, limitations,
interventions, stops, resolutions, recurrence prevention, avoided impact,
residual risks, human decisions, and evidence—so the integration layer cannot
silently drop a trust-relevant item.

## Outcome dialog boundary

WI-05 has durable Outcome JSON/Markdown and `task_report.json`/
`task_report.md` projections. `ai-finish` also contains a tested direct CLI
handoff (`deliver_direct_outcome_report`). These prove repository persistence
and stdout generation only. A caller can discard or truncate stdout, and the
Codex conversation UI receipt is external to this repository; WI-14 therefore
reports `conversationUiReceipt=not_observable` and never treats file presence
as proof that a human saw the dialog message.

This boundary applies to every owning Agent and subagent. The owner or parent
orchestrator must relay 🟢/🟡/🔴, Outcome status, concise findings, and the next
safe action into the human conversation. WI-14 records this as the required
`agentHandoffProtocol`; it is a process obligation, not a claim that a file can
authenticate UI receipt.

## Performance boundary

WI-12 is an evidence-only diagnosis. It reports measured timing, explicit wait,
repetition, and comparable baseline fields when supplied, with
`decisionImpact=none`. This final integration run has no comparable archived
before/after baseline, so runtime performance improvement is **unverified** and
no causal improvement claim is allowed. Strict quality duration and parallel
resource contention remain observations, not proof of a faster runtime.

## Re-run and interpretation

Run WI-14 after any archive or projection change. Green requires complete,
warning-free evidence; yellow means the evidence is structurally valid but a
limitation remains; red requires repairing the exact listed defect before any
completion or performance claim.
