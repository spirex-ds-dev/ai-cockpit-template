---
author: Ray
title: "Standard Adoption Guide"
description: "Evidence-backed installation, calibration, Work Item, and review guidance for adopters."
keywords:
  - adoption
  - governance
  - verification
---

# Standard Adoption Guide

<!-- semantic-domain: north-star -->
<!-- semantic-domain: product-boundary -->
AI Cockpit is a Repository Governance Layer for calibrated Human-Agent Trust. It
governs reviewable repository evidence; it is not an Agent Runtime, Workflow
Engine, or Security Sandbox.

This guide is for adopters after the installer has created
`adopt_ai_cockpit`. Complete the prerequisites and installation in
[Installation](installation.md) first. The installer-generated Contract records
the fetched pre-adoption base commit used below.

<!-- doc-domain: adoption -->
<!-- semantic-domain: installation-flow -->
## Adoption

Install from a published release into the target repository, finish
`adopt_ai_cockpit`, review the diff, then use one PR for that Adoption Work Item.
Installation places the governance runtime; it does not complete project
adaptation.

<!-- command-evidence: adopter_required -->
```sh
make ai-finish TASK=adopt_ai_cockpit
# Stop for approval before the archive-bundle commit.
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT='<pre-adoption-commit>'
```

Complete the lifecycle in this order:

1. Run local finish/archive, then stop for review.
2. Obtain explicit approval, commit the complete archive bundle, and run the PR check against the base recorded by the installer.
3. Obtain separate approval before push.
4. Create the PR without auto-merge or provider-side branch deletion, then have a human merge it.
5. Obtain approval for closure, then run:

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

Closure verifies base synchronization and deletes the local and remote Work Item
branch. See [Installation — Adoption](installation.md#phase-3-adoption) for the
full stop conditions.

<!-- doc-domain: calibration -->
## Calibration

Use a separate `configure_ai_cockpit` Work Item to review Project Profile,
Guard, quality-command, Coverage, and CI evidence. Unknown or stale evidence
blocks readiness.

<!-- command-evidence: adopter_required -->
```sh
make cockpit-doctor
make cockpit-calibrate
cp .ai/project_profile.proposed.yaml .ai/project_profile.yaml
${EDITOR:-vi} .ai/project_profile.yaml
make check-ai-project-profile
make check-ai-guard-calibration
make ai-cockpit-quality
make check-ai-adoption-ready
```

The copy is not approval by itself. A human must review the proposed facts,
resolve every `blocking:` unknown, set approved boundaries, and calibrate
quality commands, Coverage, CI, CODEOWNERS, and SECURITY.md before readiness.

<!-- doc-domain: work-item -->
<!-- semantic-domain: task-outcome-fields -->
## Work Item and Task Outcome

Every change uses one Contract, branch, Summary, PR, archive, merge, closure,
and branch cleanup. Task Outcome must retain findings, risks, stop reasons,
resolutions, prevention, verification, unknowns, human decisions, and residual
risk rather than reporting only success.

<!-- doc-domain: ci -->
## CI

Fetch full Git history and require both the public project quality target and
`check-ai-pr`. Hosted template fixtures do not prove the adopter's commands.

<!-- command-evidence: adopter_required -->
```sh
ADOPTER_REMOTE="${ADOPTER_REMOTE:?use the remote recorded in the Contract}"
ADOPTER_DEFAULT_BRANCH="${ADOPTER_DEFAULT_BRANCH:?use the default branch recorded in the Contract}"
make ai-cockpit-quality
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD "$ADOPTER_REMOTE/$ADOPTER_DEFAULT_BRANCH")"
```

<!-- doc-domain: human-approval -->
<!-- semantic-domain: human-confirmation -->
## Human approval

In an adopter project, stop for separate human decisions before commit, push,
merge, and `ai-close-work-item`, as defined in
[Installation — Adoption](installation.md#phase-3-adoption).
Automatic merge or provider-side branch deletion must not bypass lifecycle
closure.

<!-- doc-domain: target-project-adaptation -->
<!-- semantic-domain: supported-scope -->
## Target-project adaptation

Presets are starting points. Calibrate actual modules, variants, SDK/JDK,
formatter, tests, build plugins, Coverage paths, branch policy, and hosted CI.
The `generic` stack preset remains fail closed until those facts are explicit. Capability status
comes from the Capability Truth Matrix, not from this guide.
