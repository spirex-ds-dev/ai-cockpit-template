---
author: Ray
title: "Content-bound Evidence Reuse"
description: "Pure, fail-closed reuse eligibility for evidence bound to exact repository content."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: wi-08-content-bound-reuse-successor-tests
capabilityClaims:
  - repository_governance_layer
---

# Content-bound Evidence Reuse

WI-08 adds a content-specific policy on top of the versioned WI-07 binding
foundation. It answers one narrow question: does the current, attributable
content still exactly match the content covered by a binding? It does not run a
check, create a cache entry, schedule work, or grant permission to bypass
security, scope, governance, coverage, or required-check gates.

## Content identity

Use `build_content_dependency(files)` with a non-empty mapping of relative
POSIX paths to exact `bytes`:

```python
from scripts.ai_evidence_binding import build_content_dependency

dependency = build_content_dependency({
    "src/example.py": b"return 1\n",
    "tests/test_example.py": b"assert example() == 1\n",
})
```

The helper sorts paths and hashes each UTF-8 path and byte payload with
length-prefixed framing. Therefore path order, text decoding, concatenation
ambiguity, and an unrelated Git Base SHA cannot change identity for the same
covered bytes. Empty, absolute, traversal, dot-segment, backslash, duplicate,
or non-byte inputs raise `BindingError`; callers must treat that as rerun.

The resulting dependency is the WI-07 content shape:

```json
{
  "digest": "sha256:<64 lowercase hex>",
  "paths": ["src/example.py", "tests/test_example.py"]
}
```

## Decision boundary

Pass the binding and current content identity to
`decide_content_reuse(binding, current, scope_digest=..., governance_digest=..., now=...)`.
`current` must contain `content` with exactly `digest` and sorted `paths`. An
optional `baseCommit` is informational and ignored by this policy. The
security-scope digest, governance-policy digest, exact content digest, exact
path set, and unexpired binding are all required for reuse.

The result is deterministic and has the same shape as the WI-07 foundation:

```json
{"state": "fresh", "action": "reuse", "reasons": []}
```

Only an exact content, scope, governance, and freshness match returns that
pair. A changed digest or path set returns `state: stale` and
`action: rerun`. Missing, malformed, unsupported, incomplete, or unknown
inputs return `state: unknown` and `action: rerun`. Reason order is stable and
the helper does not mutate caller data.

## Base-independent reuse

Content-bound evidence remains eligible when an unrelated Base commit changes,
provided the current content dependency and mandatory scope/governance
identities still match exactly. This is the intentional difference from
diff-bound policy, which WI-09 owns. A timestamp, branch name, agent statement,
or partial file comparison can never establish content equality.

## Handoff and limits

WI-09 owns diff-bound policy and WI-10 owns environment-bound policy. Future
callers may use this decision as one input to their own verification flow, but
must still execute every required gate when the result is not exactly
`fresh`/`reuse`. This Work Item does not change `ai_verify`, the evidence schema,
the scheduler, cache behavior, provider integration, or required-check policy.
