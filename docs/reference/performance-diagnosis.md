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

The report is advisory evidence. It records observed phase and gate durations,
retry/backtrack/human-decision counts, and the top three measured bottlenecks.
Provider wait, human wait, recovery time, and token usage are `unknown` unless
an authoritative source supplies them; local elapsed time is never used as a
proxy. Events belonging to another Work Item are excluded and counted in the
source metadata. Malformed event logs fail closed.
