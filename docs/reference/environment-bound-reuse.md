---
author: Ray
title: "Environment-Bound Evidence Reuse"
description: "Allowlisted runtime, toolchain, and environment identity for fail-closed evidence reuse decisions."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: wi-10-environment-bound-reuse-successor-tests
capabilityClaims:
  - repository_governance_layer
---

# Environment-Bound Evidence Reuse

WI-10 supplies the environment-specific adapter on top of the WI-07 evidence
binding foundation. It answers only whether a previously bound result has the
same explicitly supplied runtime, toolchain, and environment identity. It does
not execute a check, persist a cache, schedule work, call a provider, or grant
permission to skip security, scope, governance, coverage, or required-check
gates.

## Snapshot contract

`build_environment_snapshot()` accepts three explicit inputs:

| Field | Meaning |
| --- | --- |
| `runtime` | Non-empty runtime identity, such as `python-3.14.4`. |
| `toolchain` | Non-empty, sorted key/value metadata for the execution toolchain. |
| `environment` | Non-empty, sorted key/value metadata for the execution environment. |

The returned object has exactly `runtime`, `toolchain`, `environment`, and
`fingerprint`. The toolchain is stored as canonical JSON and the fingerprint is
the SHA-256 digest of the canonical runtime/toolchain/environment object. Input
mappings are not mutated. `current_environment()` provides a small allowlist of
platform and Python metadata and may be extended only with explicit toolchain
values.

Secret-like keys (for example `token`, `password`, `api_key`, `credential`, or
`authorization`) are rejected. The implementation never serializes the process
environment wholesale and does not read credentials.

## Binding and decision API

```python
from datetime import UTC, datetime, timedelta

from scripts.ai_environment_reuse import (
    build_environment_binding,
    build_environment_snapshot,
    decide_environment_reuse,
)

now = datetime.now(UTC)
environment = build_environment_snapshot(
    runtime="python-3.14.4",
    toolchain={"python": "3.14.4", "runner": "pytest-9.1.1"},
    environment={"os": "darwin", "architecture": "arm64"},
)
binding = build_environment_binding(
    subject={"workItemId": "example", "evidenceId": "quality"},
    environment=environment,
    scope_digest="sha256:<64-lowercase-hex>",
    governance_digest="sha256:<64-lowercase-hex>",
    producer={"command": "pytest -q", "version": "runner-1"},
    created_at=now,
    expires_at=now + timedelta(hours=1),
)
decision = decide_environment_reuse(
    binding,
    environment,
    scope_digest=binding["scopeDigest"],
    governance_digest=binding["governanceDigest"],
    now=now,
)
```

`build_environment_binding()` delegates to the versioned WI-07 binding model,
using the `environment-bound` classification and its required `digest`,
`runtime`, and `toolchain` dependency shape. Scope and governance digests are
mandatory binding inputs and are compared by the shared foundation.

The only reusable result is:

```json
{"state": "fresh", "action": "reuse", "reasons": []}
```

| Condition | Decision |
| --- | --- |
| Exact environment dependency, scope, governance, and unexpired binding | `fresh` / `reuse` |
| Environment runtime, toolchain, or platform identity differs | `stale` / `rerun` |
| Binding is expired | `stale` / `rerun` |
| Snapshot, binding, scope, governance, or time input is missing or malformed | `unknown` / `rerun` |

Unknown is intentionally fail-closed. A caller must execute the required
operation for every result other than the exact `fresh`/`reuse` pair. The
adapter does not decide whether that operation is security-sensitive or
required; those gates remain caller-owned.

## Boundary and handoff

This Work Item defines the environment identity and deterministic decision
primitive only. WI-08 and WI-09 own other reuse conditions, while later policy
consumers may decide how to record or act on a decision. No scheduler, cache,
parallel runner, verifier integration, provider integration, or schema change
is introduced here. The shared schema and generic comparison semantics remain
owned by WI-07.

Focused coverage is in
`tests/test_ai_environment_reuse.py`, including canonical fingerprints,
immutability, all three environment mismatch classes, Unknown/malformed and
expired inputs, mandatory scope matching, secret-key rejection, and the
allowlisted current-environment projection.
