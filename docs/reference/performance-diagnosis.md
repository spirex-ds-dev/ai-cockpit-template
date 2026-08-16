---
author: Ray
title: "Performance diagnosis"
description: "Evidence-only Work Item governance-cost and bottleneck reporting."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
capabilityClaims:
  - repository_governance_layer
---

# Performance diagnosis

`scripts/ai_performance_diagnosis.py` derives a Work Item-level governance-cost
report from `target/ai_observability.jsonl`:

```sh
PYTHONPATH=scripts python scripts/ai_performance_diagnosis.py \
  --work-item <id> \
  --json-output target/performance/<id>.json \
  --markdown-output target/performance/<id>.md
```

For a comparable prior report, provide its JSON explicitly:

```sh
PYTHONPATH=scripts python scripts/ai_performance_diagnosis.py \
  --work-item <id> \
  --events target/ai_observability.jsonl \
  --baseline-report target/performance/<baseline-id>.json \
  --json-output target/performance/<id>.json \
  --markdown-output target/performance/<id>.md
```

The report is advisory evidence. It records observed phase and gate durations,
retry/backtrack/human-decision counts, and the top three measured bottlenecks.
Provider wait, human wait, recovery time, and token usage are `unknown` unless
an authoritative source supplies them; local elapsed time is never used as a
proxy. Events belonging to another Work Item are excluded and counted in the
proxy. Events belonging to another Work Item are excluded and counted in the
source metadata. Malformed event logs fail closed.

The diagnosis projection additionally records repeated quality checks only when
the same check identity is explicitly observed more than once. Explicit
`ci_wait`, `ci_wait_finished`, `resource_wait`, `resource_wait_finished`,
`contention_wait`, and `contention_wait_finished` events are kept separate from
local compute and gate duration. An unrecognised wait category is not attributed
and is reported as a limitation.

Baseline comparison is limited to matching numeric timing fields and reports
`beforeMs`, `afterMs`, `deltaMs`, and `deltaPercent`. Missing or incompatible
fields remain absent with an explicit limitation; no causal improvement claim is
generated. The source digest and deterministic sorted report fields make a run
reproducible from the same event fixture. The JSON contract is
`.ai/schemas/performance-diagnosis-report.schema.json`.

This tool explains measured cost for later human or orchestrator decisions. It
does not change gate outcomes, scheduling, trust decisions, or runtime behavior.

For the repository-local project-test optimization, capture a same-base serial
or prior-session baseline and a candidate run with the exact commit/tree and
manifest identity. `/usr/bin/time -p make project-test` supplies wall-clock
evidence; the shard receipts and `target/quality/sessions/` timing JSON supply
ownership and phase evidence. A lower wall time on this machine is a measured
local result only. It is not evidence of a cross-machine, hosted, or adopter
speedup, and it must not be reported as causal unless comparable diagnosis
reports support that claim.
