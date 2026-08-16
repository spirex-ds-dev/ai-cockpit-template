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

The report records only observed local facts: phase compute time, gate duration, gate and verification runs, retries, backtracks, and human-decision events. Events belonging to another Work Item are excluded and counted; malformed JSON fails closed.

Provider wait, human wait, recovery duration, and token usage are always `unknown` when the local source does not provide them. The report is advisory (`advisory: true`, `decisionImpact: none`) and never changes gate eligibility, scheduling, or governance decisions.

The machine-readable contract is [governance-cost-report.schema.json](../../.ai/schemas/governance-cost-report.schema.json). The digest is computed from the report content before its display timestamp, so identical evidence produces the same digest.
