---
author: Ray
title: "Governance cost metrics"
description: "Evidence-only execution-cost reporting for one AI Cockpit Work Item."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
---

# Governance cost metrics

`scripts/ai_governance_cost.py` converts the local JSONL observability stream into a versioned report for one Work Item:

```bash
python scripts/ai_governance_cost.py \
  --work-item wi-example \
  --events target/ai_observability.jsonl \
  --json-output target/governance-cost/wi-example.json \
  --markdown-output target/governance-cost/wi-example.md
```

The report records only observed local facts for one Work Item. In addition to the
WI-02 `observed` counters, the lifecycle projection contains:

- `time.totalElapsedMs`: the explicit `work_item_finished.durationMs` value (the
  maximum when more than one finish event is present).
- `time.agentActiveMs` and `time.phaseDurationsMs`: summed
  `lifecycle_phase_finished` durations.
- `time.verificationMs`: durations from quality verification check results.
- `time.ciWaitMs`, `time.humanWaitMs`, and `time.recoveryRetryMs`: sums only
  when an event explicitly declares the category and duration.
- `topBottlenecks`: at most three deterministic entries from measured phases,
  check results, explicit waits, and explicit retry recovery durations.

Wait evidence uses `wait_finished` with `fields.category` set to `ci` or
`human` (the equivalent `ci_wait_finished` and `human_wait_finished` event
types are also accepted). A retry duration is recorded only when the retry
event has `durationMs` or `fields.durationMs`.

Events belonging to another Work Item are excluded and counted; malformed JSON
fails closed. Missing durations and categories remain `unknown`; local phase
time is not used as a proxy for provider or human wait.

Provider wait, human wait, recovery duration, and token usage are always `unknown` when the local source does not provide them. The report is advisory (`advisory: true`, `decisionImpact: none`) and never changes gate eligibility, scheduling, or governance decisions.

The machine-readable contract is [governance-cost-report.schema.json](../../.ai/schemas/governance-cost-report.schema.json). The digest is computed from the report content before its display timestamp, so identical evidence produces the same digest. The report remains advisory (`advisory: true`, `decisionImpact: none`) and cannot alter gates, scheduling, or lifecycle decisions.
