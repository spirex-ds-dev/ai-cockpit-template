---
title: Provider-Backed Governance Validation
author: Ray
description: Read-only GitHub receipt collection for provider-governance facts.
---

# Provider-Backed Governance Validation

Use the command below to collect a point-in-time GitHub receipt for one real
pull-request and release route. It only issues `gh api` GET requests; it never
changes branch protection, rulesets, CODEOWNERS, access, PR state, tags, or
releases.

```sh
python scripts/provider_backed_governance_validation.py \
  --repository spirex-ds-dev/ai-cockpit-template \
  --pull-request 561 \
  --tag v0.5.47 \
  --output target/provider-backed-governance-validation/receipt.json
```

The receipt has one fact for each of: PR creation, Required Checks, Branch
Protection, CODEOWNERS, Review Approval, merge, merge SHA, remote branch
cleanup, tag, release, release asset, provider identity, and provider audit
evidence. Every `provider_verified` fact records its provider resource ID and
observation time; facts tied to a Git object also record its SHA.

## Evidence states

- `provider_verified`: GitHub returned the specific provider resource.
- `repository_recorded_only`: a repository file records a claim, but GitHub was
  not observed. The current command does not promote this state.
- `local_provider_simulation`: a local test or simulation. The live command
  never emits this state.
- `not_run`: GitHub could not expose the resource or the query could not run.
- `not_claimed`: GitHub was observed, but it did not establish the requested
  capability (for example, no APPROVED review or no required-check policy).

These states are intentionally non-interchangeable. A local Git username is
not provider authentication; approval text in a PR is not an approved review;
a remote branch is not proof that a PR was created; a tag is not a Release; and
a Release page without an asset digest is not release-asset integrity evidence.

If GitHub returns no resource (such as an unprotected branch or absent
CODEOWNERS), keep that `not_run` or `not_claimed` result. Do not change provider
configuration merely to obtain a stronger result.
