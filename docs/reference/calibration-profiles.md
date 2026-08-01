---
author: Codex
title: "Calibration Profiles"
description: Proportional Lite, Standard, and Strict control requirements for project calibration.
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - project_calibration_profile_proposal
keywords:
  - ai-cockpit
  - calibration
  - governance-profile
---

# Calibration Profiles

Calibration Profiles select the controls an adopter must evidence. They are
separate from Work Item quality routing: calibration describes the repository's
standing governance boundary, while quality routing selects checks for one diff.
The template provides the proposal and validation policy; this is not proof of
adopter installation or activation in a target repository.

The levels are cumulative: `lite < standard < strict`.

| Level | Required controls added at this level |
| --- | --- |
| Lite | source, test, generated, and protected paths; quality command; default branch; project owner; reviewer; major unknowns |
| Standard | file ownership, scenario coverage, destructive-change, dependency, CI, public API, lifecycle, and delegated-evidence policies |
| Strict | Reviewer/Owner separation, external identity evidence, release evidence, SBOM, provenance, signed-tag and branch-protection evidence, audit retention, incident/exception policy |

Lite deliberately defers supply-chain, release-attestation, dual-person,
enterprise-audit, and external-identity controls. Deferred does not mean proven
unnecessary; it records that the selected calibration level does not require them.

## Selection evidence

`.ai/project_profile.yaml` records `calibrationProfile.level`, `selectedBy`,
`selectedAt`, `reasons`, `requiredControls`, and `deferredControls`. The control
lists must exactly match `.ai/calibration/profiles.yaml`; hand-written omissions
or additions fail closed. Generated proposals use `pending_human` and a pending
timestamp so they cannot impersonate completed human selection.

Validate a confirmed selection with:

```sh
make check-ai-calibration-profile
make check-ai-calibration-profile ARGS="--previous-level standard"
```

`selectedBy: human` records the authority class only. It does not authenticate an
identity or prove external approval. Supply the previous level from reviewed base
evidence when validating a transition; without that input the validator does not
claim that repository history was inspected.

## Transitions and recovery

Lite→Standard and Standard→Strict are monotonic upgrades. A downgrade requires a
transition record containing the original and new levels, reason, the exact
controls being closed, risk acceptor, and effective path scope. Missing,
contradictory, or incomplete evidence blocks validation. Restore the previous
level or complete the bounded transition record to recover.

This feature validates repository evidence. It does not provide an identity
system, compliance certification, release attestation, or proof that an adopter
executed every delegated tool.
