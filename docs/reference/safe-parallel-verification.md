---
author: Ray
title: "Safe parallel verification"
description: "Bounded conflict-aware execution for independent verification jobs."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
---

# Safe parallel verification

`scripts/ai_parallel_verification.py` accepts an argv-only plan and runs independent jobs concurrently:

```bash
python scripts/ai_parallel_verification.py \
  --plan plan.json \
  --cwd . \
  --output target/parallel-verification/report.json
```

`maxWorkers` is bounded to 1–8. Jobs are placed into deterministic batches. Any overlapping declared scope is serialized; an empty scope is treated as conflicting with every job, so independence is never inferred. Each result records its command, scope, status, return code, duration, stdout, and stderr. A failed job is recorded without hiding other results; malformed plans fail before any command executes.

The plan contract is [.ai/schemas/parallel-verification-plan.schema.json](../../.ai/schemas/parallel-verification-plan.schema.json). The runner uses argv arrays and `subprocess.run` without a shell, and does not provide scheduling or network behavior.
