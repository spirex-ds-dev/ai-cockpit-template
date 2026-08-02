---
author: Ray
title: "External Identity Boundary"
description: "Identity levels and evidence requirements for approval records."
audience:
  - adopter
  - maintainer
status: reference
authority: canonical
lastVerifiedBy: tests/test_external_identity.py
capabilityClaims:
  - external_identity_boundary
keywords:
  - ai-cockpit
  - identity
  - approval-evidence
---

# External Identity Boundary

AI Cockpit validates the shape and declared strength of approval evidence. It
does not authenticate a person, contact an identity provider, or turn a name in
a repository file into external identity proof.

## Identity levels

| Level | Meaning | High-risk approval |
| --- | --- | --- |
| `self_declared` | An agent or text claims that an actor approved. | Never sufficient. |
| `repository_recorded` | A repository record names an actor. | Never sufficient; display as `repository_recorded_only`. |
| `provider_verified` | A hosting provider record binds actor, repository, review or protected approval, and commit. | Eligible when the evidence and scope are complete. |
| `enterprise_verified` | An SSO, IAM, corporate approval, or audit system supplies an external reference. | Eligible when the evidence and scope are complete. |
| `direct_user_authorized` | A user directly authorizes one exact destructive scope when independent Provider review is unavailable to that same identity. | Eligible only with the required direct instruction reference, digest, timestamp, and exact scope; it is not an independent review. |

The level is an evidence classification, not a claim that AI Cockpit performed
the external verification. The external system remains the evidence producer.

## Approval Evidence schema

Approval records use `.ai/trust/schema/approval.schema.json`. A provider-bound
destructive approval looks like this:

```json
{
  "schemaVersion": 1,
  "approvalType": "destructive_change",
  "identityLevel": "provider_verified",
  "actor": "github-user",
  "provider": "github",
  "evidence": {
    "repository": "org/repo",
    "pullRequest": 123,
    "reviewId": 456,
    "commitSha": "0123456789abcdef0123456789abcdef01234567"
  },
  "scope": ["src/api/public.py"]
}
```

`provider_verified` requires a provider, repository, pull request, commit SHA,
and at least one review, environment approval, or ruleset identifier.
`enterprise_verified` requires a provider, enterprise system, and external
reference. Every level requires a non-empty, exact scope.

`direct_user_authorized` requires `provider: null`, a non-empty actor, and
these evidence fields: `directUserInstructionRef`, a `sha256:`
`directUserInstructionDigest`, and ISO-8601 `authorizedAt`. It must not carry
a repository, pull request, review, ruleset, environment, commit, or
enterprise identifier. This record proves only that the repository captured a
direct user instruction for the exact scope; it does not prove the user's
identity, create a GitHub review, or replace independent Provider evidence.

## Contract integration

When `destructiveChangePolicy.allowed` and `requiresHumanApproval` are both
true, the existing `approvalEvidence` decision record must contain an
`identityEvidence` object that passes the Approval Evidence schema and the
high-risk semantic check:

```json
{
  "approved": true,
  "approvedBy": "github-user",
  "reason": "Provider review covers the destructive scope.",
  "identityEvidence": {"schemaVersion": 1, "approvalType": "destructive_change"}
}
```

The abbreviated object above is illustrative only; all schema fields and
level-specific evidence remain required. A legacy `approvedBy: Ray` record is
retained as repository workflow history but is reported as
`repository_recorded_only` and cannot authorize a destructive change.

When the sole authenticated GitHub identity cannot approve its own pull
request, a Contract may instead use a complete `direct_user_authorized`
record. The Summary and Outcome must render that lower assurance label exactly
and must not say that an external review was completed.

`restrictedWriteApproval` remains a non-destructive repository workflow
record. Its `approvedBy` field records the stated decision; it does not
authenticate that actor.

## Non-capabilities

This boundary does not provide SSO, IAM, GitHub identity lookup, branch
protection, release attestation, immutable audit, or enterprise compliance.
It validates supplied references and prevents repository-only assertions from
being represented as stronger evidence.
