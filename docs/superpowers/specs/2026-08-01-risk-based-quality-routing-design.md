---
author: Codex
title: "Risk-Based Quality Routing Design"
description: "Historical design record for selecting Light, Standard, or Strict governance with release-specific verification escalation."
---

# Risk-Based Quality Routing Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Status

Approved for WI-03 implementation under the user's standing authorization for
in-scope engineering and governance decisions. This document is an
implementation record, not runtime instruction.

## Problem

AI Cockpit already owns Fast, Full, and Release quality graphs, but the default
Work Item finish path always selects the same broad graph. Separate path-scope
and verification-policy classifiers use different vocabularies and do not bind
the Contract or default execution. Consequently, low-risk documentation work is
needlessly expensive while the evidence for any downgrade is implicit.

## Decision

Introduce one deterministic governance-profile selector with the ordered
profiles `light < standard < strict`. The selector reads a versioned repository
policy, classifies changed Git paths, evaluates the active Contract, detects
release-owned operations and resources, and emits a JSON receipt. A release
context adds release-preflight and distribution verification to Strict; it is
not a fourth profile. All consumers use that result:

- `determine_quality_scope.py` remains available as a compatibility projection;
- `ai_verification_policy.py` uses the same three-profile vocabulary and
  explicit operation escalation;
- `ai-cockpit-quality` selects an existing quality ownership graph;
- Contract v2 records the selected profile and any bounded override evidence.

The router selects; existing Make targets continue to own and execute gates.
No gate command is copied into the router.

## Profiles and execution groups

| Profile | Typical evidence | Existing execution ownership |
| --- | --- | --- |
| Light | documentation, comments, non-executable examples, formatting-only changes | `quality-fast` |
| Standard | ordinary source, tests, bug fixes, small refactors | `quality-fast`, project tests, reference-impact, full test-weakening |
| Strict | governance, CI, installer, security, destructive behavior, public API, dependency, migration, calibration, evidence schemas | `quality-full` |

Release metadata, tags/workflows, SBOM, provenance, assets, distribution, or
release claims select `strict` plus the `release_preflight` and `distribution`
verification escalations. Non-release Strict work does not run that graph.

Unknown paths select at least Standard. Mixed changes select the highest profile.
Explicit requests may raise but may not lower the automatically selected profile.

## Policy format

`.ai/quality/governance-routing.yaml` is the policy SSOT. It declares:

- a schema version and the fixed three-profile order;
- evidence-only lifecycle patterns that remain in receipts without raising risk;
- exact paths and path prefixes for each profile;
- required Make ownership groups for each profile;
- the conservative unknown-path profile;
- release and protected-surface patterns that derive operation and verification
  escalation ahead of broader documentation or source patterns.

The loader rejects missing keys, unknown profiles, unsafe paths, duplicate or
unordered profile declarations, and malformed group mappings. Policy failure is
an error, never a Light fallback.

## Contract evidence and overrides

Contract v2 accepts:

```json
{
  "governanceProfile": {
    "selected": "strict",
    "source": "automatic",
    "reasons": ["governance policy changed"],
    "override": null
  }
}
```

An automatic record must have a null override. A `human_override` record must
identify the lower selected profile, reason, acknowledged risks, checks not run,
approval evidence, and either a current-Work-Item scope or an expiry. The router
validates that the record belongs to the active Work Item and has not expired.
Malformed, stale, or mismatched evidence restores the automatic result and
reports why. Repository evidence does not authenticate the human identity;
external identity proof remains outside WI-03.

## Data flow

1. Resolve and validate repository, base, head, policy, and optional Contract.
2. Obtain changed paths from Git or an explicit test-only path list.
3. Normalize paths and reject absolute paths, traversal, or repository escapes.
4. Classify every path, apply precedence, and select the highest profile.
5. Apply Contract evidence only when it is structurally valid and bounded.
6. Apply an explicit CLI request only when it preserves or raises the result.
7. Emit a deterministic receipt containing inputs, paths, per-path reasons,
   automatic and selected profiles, override disposition, and required groups.
8. Make invokes the existing graph named by the receipt.

## Compatibility

The legacy quality-scope interface keeps its schema and explicit
`fast|full|release` quality modes. The shared router maps Light to Fast and
Standard or Strict to Full; a detected release operation additionally selects
the release verification graph. The generic `quality` alias remains Full for
callers that explicitly chose it; only the AI Cockpit default entrypoint becomes
evidence-routed.

Installed adopters receive the policy, router, compatibility adapter, and Make
entrypoint together. Missing installed assets fail closed instead of silently
falling back to a weaker graph.

## Failure and security boundaries

- Invalid Git bases, malformed YAML, missing Contract fields, expired override
  evidence, traversal, and symlink escape fail closed.
- An empty diff is not treated as proof of low risk; it selects at least Standard
  unless an explicit governed lifecycle supplies a stronger fact.
- The receipt is deterministic repository evidence, not an authorization token.
- Routing does not change provider checks, branch protection, release authority,
  or human identity authentication.

## Verification strategy

Red-first tests cover each of the three profiles, release-context derivation,
mixed and unknown changes, input ordering, malformed policy, traversal and
symlink escape, Contract schema, valid and stale overrides, CLI escalation,
forbidden downgrade, legacy output, Make dry-runs, quality ownership invariants,
and installed-adopter behavior. The Work Item then runs the focused suites and
the Strict finish graph required by its own changes.

## Rejected alternatives

1. A second quality execution system was rejected because it would duplicate
   commands and allow ownership drift.
2. CI-only routing was rejected because local finish and installed adopters need
   the same deterministic decision.
3. Permanent profile exceptions were rejected because downgrade evidence must be
   bounded to an expiry or the current Work Item.
