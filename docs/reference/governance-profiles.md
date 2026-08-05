---
author: Ray
title: "Governance Profiles"
description: Risk-based Light, Standard, and Strict routing with operation-specific verification escalation.
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - risk_based_quality_routing
keywords:
  - ai-cockpit
  - governance-profile
  - quality-routing
---
# Governance Profiles

AI Cockpit selects the smallest quality graph justified by repository evidence.
Profiles are ordered `light < standard < strict`; mixed changes take the highest
result, and unknown or empty path evidence defaults to at least Standard. Release
is an operation class that adds checks to Strict; it is not a fourth profile.

## Profiles

| Profile | Typical changes | Dispatch target |
| --- | --- | --- |
| Light | documentation, comments, non-executable examples, formatting-only work | `quality-fast` |
| Standard | ordinary source, tests, bug fixes, and small refactors | `quality-standard` |
| Strict | governance, CI, installer, security, dependency, destructive/public API, migration, calibration, or evidence-schema work | `quality-full` |

`quality-standard` reuses Fast, the project test owner, reference-impact, and
full test-weakening checks. Strict uses Full. A Strict Work Item whose operation,
scope, resource claim, or capability claim is release-related also runs
`quality-release` for release-preflight and distribution verification. `make quality` remains a compatibility alias for Full;
`make ai-cockpit-quality` is the evidence-routed Work Item entrypoint.

## Contract evidence

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

The router reads `.ai/quality/governance-routing.yaml`, compares the Contract
base with committed, staged, unstaged, and untracked paths, and writes
`target/quality/governance-profile.json`. The receipt records the automatic and
selected profiles, sorted paths and reasons, required groups, dispatch target,
and override disposition. Generated current-status, Work Item start receipt,
active Contract and Summary, current Outcome, human task report, and archive
projections remain visible evidence but do not raise the profile by themselves.
These are exact lifecycle projections listed in `evidenceOnlyPatterns`; the
rule does not apply to arbitrary `.ai/**` files. An evidence-only diff defaults
to Standard, never Light, so it is not a completion or quality-downgrade path.
Any documentation change combined only with these projections can select Light
and dispatch `quality-fast`. Any Strict implementation path, release-owned
resource, release context, malformed policy, unsafe path, or invalid Git base
retains conservative escalation or fails closed.

The receipt carries `operationClasses`, `verificationEscalations`, and their
evidence reasons. `release` is not an accepted governance-profile input.
Non-release Strict work never acquires the release graph merely because of its
governance intensity.

Before the first Work Item exists, an installed adopter has no Contract base.
In that bounded case the router uses `HEAD` as the baseline and still includes
staged, unstaged, and untracked installer changes. An explicit `--base` or an
active Contract `baseCommit` remains authoritative; an invalid explicit base
fails closed.

Run the default or an explicit upward escalation with:

```sh
make ai-cockpit-quality CONTRACT=.ai/work-items/active/<task>.contract.json
make ai-cockpit-quality GOVERNANCE_PROFILE=strict
```

An explicit profile cannot lower the automatic result. A lower profile requires
a `human_override` Contract record with approval evidence, reason, acknowledged
risks, checks not run, and either an expiry or exact current-Work-Item scope.
Expired, incomplete, or mismatched evidence is rejected and the automatic
profile is restored. Overrides never become permanent policy exceptions.

## Boundaries

The receipt is repository evidence, not an authorization token. AI Cockpit does
not authenticate the person named by approval evidence, change hosted branch
protection, prove semantic risk from paths alone, or make cached/local results
equivalent to release evidence. Adopters must configure their release check;
an unconfigured Release target fails closed. Adopter-specific Strict checks may
be supplied through `AI_COCKPIT_STRICT_CHECK`; Work Item lifecycle gates remain
independently enforced by `ai-finish` and are not duplicated in that command.
