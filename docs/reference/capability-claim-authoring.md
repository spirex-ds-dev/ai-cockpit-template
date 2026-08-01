---
author: Ray
title: "Capability Claim Authoring"
description: "How to bind public capability language to current Capability Truth evidence."
audience:
  - adopter
  - maintainer
status: reference
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - capability_claim_binding
keywords:
  - ai-cockpit
  - capability-claims
  - evidence-governance
---

# Capability Claim Authoring

AI Cockpit verifies that strong current capability wording in README and
canonical public documentation names evidence in the
[Capability Truth Matrix](capability-truth-matrix.md). This is a lexical,
repository-local check; it does not prove semantic completeness, translation
quality, production readiness, or enterprise readiness.

## When a binding is required

A binding is required when current public prose uses configured claim terms.
English terms include `supports`, `prevents`, `blocks`, `guarantees`,
`verifies`, `detects`, `protects`, `ensures`, `implemented`,
`production-ready`, and `enterprise-ready`, including ordinary inflections.
The checker also recognizes their configured Japanese and Simplified Chinese
counterparts.

Use the narrowest matrix row that supports the prose. Do not bind a broad
repository capability merely to silence an error when the paragraph describes
a narrower feature.

## Binding syntax

For a document-wide declaration, add exact matrix IDs to YAML front matter:

```yaml
capabilityClaims:
  - reference_impact_gate
  - test_weakening_guard
```

For a claim adjacent to one section, use an inline marker:

```markdown
<!-- capability-claim: reference_impact_gate -->
```

Both forms may appear together. IDs are exact and case-sensitive; aliases and
hyphen/underscore normalization are not accepted.

## State and evidence rules

| Effective state | Public wording rule |
| --- | --- |
| `implemented` | Current repository capability wording is allowed within the row's limitations. |
| `adopter_installed` | Current wording is allowed only within the row's stated installed/adopter evidence boundary. |
| `template_only` | State that the template provides the material and that this does not prove adopter installation. |
| `planned` | Use explicit planned or future wording; do not present it as available now. |
| `evidence_stale` | No public claim is allowed until evidence bytes and the row digest are regenerated and verified. |

Every bound row must exist, have non-empty limitations, and pass the existing
matrix validation. Source/test file byte drift makes the effective state
`evidence_stale`, even when the stored status still says otherwise.

## Multilingual scope

English, Japanese, and Simplified Chinese siblings must declare identical
capability ID sets. A translation may choose natural local phrasing, but it
cannot add or omit capability scope. Derived translation siblings of a
canonical current page are checked together with the canonical page.

## Exclusions

Archived Work Items, registered implementation records, supporting evidence,
and the generated `capability-truth-matrix.md` projection are not scanned as
independent public claims. The projection is derived directly from the JSON
truth source. Exclusion does not authorize copying historical language into a
current README or canonical page without a binding.

## Repairing a failure

1. Read the reported path and claim term or capability ID.
2. Choose the exact matrix row whose claim and limitations cover the prose.
3. Add YAML or inline binding syntax to every language sibling.
4. Narrow template-only or planned wording when required.
5. If evidence is stale, verify the changed behavior and regenerate the matrix;
   do not merely edit a digest.
6. Run `make check-capability-claims` or `make check-docs-metadata`.
