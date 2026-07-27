---
author: Codex
title: "Instruction Traceability"
description: "Bidirectional traceability from explicit instructions to plan, implementation, acceptance, and verification evidence."
---

# Instruction Traceability

The remediation plan uses a small, reviewable JSON manifest at
`docs/reference/remediation-instruction-traceability.json`. Each stable
instruction ID maps forward to plan Work Items, Contract records,
implementation evidence, acceptance evidence, and verification commands.

The checker also works in reverse: every referenced Work Item must occur in
the declared plan, every referenced evidence path must exist, and every named
deliverable must either appear in implementation evidence or carry an
explicit no-change rationale. A no-change rationale records a gap; it does
not make the Work Item complete or unblock release.

Archived evidence is resolved deterministically when an older manifest still
refers to an `active/` Contract or Summary path. The checker also validates
the SHA-256 bindings in `archive/index.json` and each Archive Manifest, so a
post-finish edit cannot silently leave stale discovery evidence.

Hosted performance evidence uses the registered `hostedPerformanceEvidence`
Summary shape. Each scenario must declare `pass`, `not_run`, or `fail`, with a
reason for non-passing scenarios and a comparison rule that prevents an
unmeasured performance claim. Unknown ad-hoc Summary fields remain invalid.

Run:

```sh
make check-instruction-traceability
```

This is a deterministic structural gate. It does not claim to understand all
natural-language requirements. A reviewer or plan author must first turn each
release-relevant instruction into a structured record; the gate then fails
closed when that record loses its plan, implementation, acceptance, or
verification link. This boundary is intentional: evidence is checked rather
than inferred from an agent's self-declaration.

The mechanism is additive to Work Item governance. Each corrective change
still requires its own Contract, Summary, focused and full verification,
dedicated branch, PR, merge, `make ai-close-work-item`, and branch cleanup.
