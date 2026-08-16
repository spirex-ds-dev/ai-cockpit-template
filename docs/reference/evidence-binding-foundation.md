---
author: Ray
title: "Evidence Binding Foundation"
description: "Versioned, fail-closed identity metadata for future evidence reuse decisions."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: wi-07-evidence-binding-tests
capabilityClaims:
  - repository_governance_layer
---

# Evidence Binding Foundation

WI-07 provides the shared identity boundary needed by later reuse Work Items.
It records what an evidence result depends on and answers one narrow question:
does the supplied binding still exactly match the current inputs and remain
unexpired? It does not execute a check, create a cache, schedule work, or grant
permission to bypass security, scope, governance, coverage, or required-check
gates.

The machine contract is
`.ai/schemas/evidence-binding.schema.json`. A binding has:

- `classification`: one of `content-bound`, `diff-bound`, or
  `environment-bound`;
- `dependencies`: the metadata for the selected classification;
- `scopeDigest` and `governanceDigest`: mandatory security and policy identity
  for every classification;
- `producer`, `createdAt`, and `expiresAt`: provenance and bounded freshness;
- `bindingId`: a deterministic digest of all other binding fields.

## Python API

```python
from datetime import UTC, datetime, timedelta

from scripts.ai_evidence_binding import build_binding, decide_reuse

now = datetime.now(UTC)
binding = build_binding(
    subject={"workItemId": "example", "evidenceId": "quality"},
    classification="diff-bound",
    dependencies={
        "diff": {
            "baseCommit": "<40-hex-commit>",
            "headCommit": "<40-hex-commit>",
            "changedPathsDigest": "sha256:<64-lowercase-hex>",
        }
    },
    scope_digest="sha256:<64-lowercase-hex>",
    governance_digest="sha256:<64-lowercase-hex>",
    producer={"command": "pytest -q", "version": "runner-1"},
    created_at=now,
    expires_at=now + timedelta(hours=1),
)

decision = decide_reuse(
    binding,
    {
        "dependencies": binding["dependencies"],
        "scopeDigest": binding["scopeDigest"],
        "governanceDigest": binding["governanceDigest"],
    },
    now=now,
)
```

`validate_binding()` raises `BindingError` for malformed or tampered records.
`decide_reuse()` converts every validation or current-input problem into a
machine-readable fail-closed result:

```json
{"state": "fresh", "action": "reuse", "reasons": []}
```

Only an exact dependency, scope, governance, and freshness match returns this
result. Expired or mismatched evidence returns `state: stale` and
`action: rerun`; missing, malformed, or Unknown inputs return `state: unknown`
and `action: rerun`. Reason order is stable: classification dependency,
security scope, governance policy, then expiry. A caller must treat any result
other than the exact `fresh`/`reuse` pair as a full rerun requirement.

## Handoff to WI-08/09/10

Later Work Items may use this model as input to their own policy-specific
reuse decisions. They must bind all inputs relevant to their operation, retain
their own security/scope/governance checks, and execute every required check
when this foundation returns Unknown or rerun. This Work Item intentionally
does not modify `ai_verify`, verification context, cache behavior, or any
parallel scheduler.

The binding is repository-local and deterministic. Timestamps are freshness
limits only; they cannot make an otherwise incomplete or mismatched binding
reusable. The schema and API are versioned so a future incompatible contract
can require an explicit migration instead of silently accepting old evidence.
