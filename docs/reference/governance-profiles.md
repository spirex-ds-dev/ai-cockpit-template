---
author: Ray
title: "Governance Profiles"
description: Risk-based Lite, Standard, Strict, and Release quality routing for AI Cockpit Work Items.
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords:
  - ai-cockpit
  - governance-profile
  - quality-routing
---
# Governance Profiles

AI Cockpit selects the smallest quality graph justified by repository evidence.
Profiles are ordered `lite < standard < strict < release`; mixed changes take the
highest result, and unknown or empty path evidence defaults to at least Standard.

## Profiles

| Profile | Typical changes | Dispatch target |
| --- | --- | --- |
| Lite | documentation, comments, non-executable examples, formatting-only work | `quality-fast` |
| Standard | ordinary source, tests, bug fixes, and small refactors | `quality-standard` |
| Strict | governance, CI, installer, security, dependency, destructive/public API, migration, calibration, or evidence-schema work | `quality-full` |
| Release | release identity, workflow, SBOM, provenance, assets, or distribution | `quality-release` |

`quality-standard` reuses Fast, the project test owner, reference-impact, and
full test-weakening checks. Strict and Release reuse the existing Full and
Release owners. `make quality` remains a compatibility alias for Full;
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
and current outcome files remain visible evidence but do not raise the profile by themselves; an
evidence-only diff defaults to Standard. Unsafe paths, invalid Git bases, and
malformed policy fail closed.

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
