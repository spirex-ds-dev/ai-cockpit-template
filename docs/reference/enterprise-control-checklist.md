---
author: Ray
title: "Enterprise Control Boundary Checklist"
description: "Adopter checklist for separating repository governance evidence from external enterprise controls."
keywords:
  - ai-cockpit
  - enterprise
  - compliance
  - adopter
---

# Enterprise Control Boundary Checklist

This checklist is an adoption handoff, not a compliance certificate. AI Cockpit can record repository-local Contracts, checks, review decisions, PRs, release evidence, and lifecycle closure. The adopter must independently configure and supply current external evidence for enterprise controls.

[`enterprise-control-matrix.json`](enterprise-control-matrix.json) is an **observed control evidence** inventory, not a compliance score. Each control has a provider, resource, required state, observed state, evidence type, verification time, owner, limitation, and expiration. Until a current external receipt is supplied, its only derived state is `not_verified`. `observed` means that one scoped, time-bound external receipt was evaluated; it does not mean compliant, certified, or enterprise-ready.

| Control area | Repository-local evidence | Adopter/provider evidence required | Default state |
| --- | --- | --- | --- |
| Identity and authorization | Reviewer/decision metadata | IdP, access lifecycle, least privilege | `not_verified` |
| Required review and branch protection | Contract scope, PR and checks | Provider rules and enforcement | `not_verified` |
| Separation of duties | Recorded roles and approvals | Organization role policy | `not_verified` |
| Signing and retention | Signature/checksum checks when present | Trusted keys, protected tags, retention | `not_verified` |
| Secrets and audit log | Secret/supply-chain checks | Secret manager, rotation, immutable audit retention | `not_verified` |
| Production isolation | Repository documentation boundary | Production-environment isolation evidence | `not_verified` |
| SBOM and provenance | Generated reports and scan results | Independent review, deployment provenance, remediation | `not_verified` |

The repository does not establish SOC 2, ISO 27001, SLSA, complete prompt-injection defense, trusted identity, runtime sandboxing, immutable audit, legal compliance, or production readiness. Any such claim requires separate, current external evidence.

Japanese and Chinese readers should use the same boundary semantics in the localized README and installation documentation; this work item does not constitute the mandatory WI-16 Japanese capability assessment.
