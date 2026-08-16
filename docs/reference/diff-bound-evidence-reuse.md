---
author: Ray
title: "Diff-Bound Evidence Reuse Policy"
description: "Exact changed-path and source-revision identity for bounded evidence reuse decisions."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: wi-09-diff-bound-reuse-tests
capabilityClaims:
  - repository_governance_layer
---

# Diff-Bound Evidence Reuse Policy

WI-09 adds a local policy for evaluating the `diff-bound` classification from
the WI-07 evidence-binding foundation. It answers only whether a supplied
binding has the same source revision, changed-path set, security scope, and
governance policy as the current input. It does not execute a check, manage a
cache, schedule work, or authorize bypassing a required verification gate.

## Current diff input

`build_current_diff()` creates the policy input with these fields:

| Field | Requirement |
| --- | --- |
| `baseCommit` | Exact 40-character lowercase source base commit. |
| `headCommit` | Exact 40-character lowercase source head commit. |
| `changedPaths` | Repository-relative POSIX path list; an empty list represents a clean diff. |
| `scopeDigest` | Mandatory `sha256:` security/scope identity. |
| `governanceDigest` | Mandatory `sha256:` policy identity. |

Changed paths are normalized to POSIX form, sorted, and treated as an
order-independent set. Absolute paths, traversal (`..`), empty paths, path
separator ambiguity, and duplicates after normalization are rejected. The
digest is the canonical JSON digest of the normalized list. A changed file
being added, removed, or renamed therefore produces a different identity and
requires rerunning the evidence producer.

## Decision boundary

```python
from scripts.ai_diff_bound_reuse import build_current_diff, decide_diff_reuse

current = build_current_diff(
    base_commit="<40-hex-base>",
    head_commit="<40-hex-head>",
    changed_paths=["src/app.py", "tests/test_app.py"],
    scope_digest="sha256:<64-lowercase-hex>",
    governance_digest="sha256:<64-lowercase-hex>",
)
decision = decide_diff_reuse(binding, current, now=now)
```

Only an exact source, path, scope, governance, and unexpired binding returns:

```json
{"state": "fresh", "action": "reuse", "reasons": []}
```

Any other result is a full rerun requirement. A source or policy mismatch is
`state: stale`; a missing, malformed, or unknown current input or binding is
`state: unknown`. Both use `action: rerun` and stable reason codes. Timestamps
only enforce the expiry boundary and can never make an incomplete or mismatched
diff reusable.

## Integration boundary

The API is pure and does not mutate its binding or current input. Existing
verification runners remain responsible for executing all required checks and
for enforcing security, scope, governance, coverage, and review gates. WI-08
and WI-10 may compose this policy for their own classifications, but neither
this Work Item nor the foundation grants execution authority, adds a cache or
scheduler, or changes `ai_verify` behavior.
