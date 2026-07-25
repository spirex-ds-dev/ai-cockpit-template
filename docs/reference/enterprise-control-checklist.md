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

This checklist is an adoption handoff, not a compliance certificate. AI Cockpit can record repository-local Contracts, checks, review decisions, PRs, release evidence, and lifecycle closure. The adopter must independently configure and verify enterprise controls.

Use only the status values in [`enterprise-control-matrix.json`](enterprise-control-matrix.json): `external_control_required`, `configured`, `verified`, `not_configured`, `not_applicable`, and `unknown`. `unknown` is not equivalent to `not_applicable` or `verified`.

| Control area | Repository-local evidence | Adopter/provider evidence required | Default status |
| --- | --- | --- | --- |
| Identity and authorization | Reviewer/decision metadata | IdP, access lifecycle, least privilege | `external_control_required` |
| Required review and branch protection | Contract scope, PR and checks | Provider rules and enforcement | `external_control_required` |
| Separation of duties | Recorded roles and approvals | Organization role policy | `external_control_required` |
| Signed commits/tags and immutable release | Signature/checksum checks when present | Trusted keys, protected tags, retention | `external_control_required` |
| Secrets and audit retention | Secret/supply-chain checks | Secret manager, rotation, immutable audit retention | `external_control_required` |
| Data classification and transfer | Repository documentation boundary | Legal/provider policy and approved transfer paths | `external_control_required` |
| Incident response and legal hold | Findings and stop records | Runbooks, ownership, preservation process | `external_control_required` |
| SBOM, provenance, dependency/vulnerability | Generated reports and scan results | Independent review, deployment provenance, remediation | `external_control_required` |

The repository does not establish SOC 2, ISO 27001, SLSA, complete prompt-injection defense, trusted identity, runtime sandboxing, immutable audit, legal compliance, or production readiness. Any such claim requires separate, current external evidence.

Japanese and Chinese readers should use the same boundary semantics in the localized README and installation documentation; this work item does not constitute the mandatory WI-16 Japanese capability assessment.
