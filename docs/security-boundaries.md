---
author: Ray
title: Input Trust and Security Boundaries
description: Local input trust classification and fail-closed authority boundaries.
keywords:
  - security
  - prompt-injection
  - input-trust
  - authority-boundary
---
# Input Trust and Security Boundaries

The input-trust classifier treats content and execution authority as separate facts. A string may contain instructions without being allowed to authorize an operation.

## Source and trust model

`human` input is a trusted request candidate and has `human_request` authority for review, but it is not automatic approval for a high-risk operation. `repository`, `issue`, `web`, `log`, `dependency`, `tool`, and `generated` input is untrusted content with `none` instruction authority. All source records state whether instructions may be present and retain external metadata separately from the content classification.

The local implementation is deterministic and fail-closed. It reports `detected`, `contained`, `blocked`, `human_confirmation_required`, `not_detected`, or `out_of_scope`. Detection indicators include direct and mixed-language requests, hidden HTML, encoded content, Unicode directionality, nested quotes, CI annotations, and forged approval or override language.

## High-risk operations

Before write, delete, push, merge, release, secret access, or permission-changing operations, the caller must re-evaluate the operation. Untrusted content can never approve the operation. The current re-evaluation helper always returns `allowed: false` and requires an explicit policy decision; this keeps the boundary fail-closed while later Work Items add broader lifecycle integration.

## Limitations

This classifier is a local heuristic and is not a complete prompt-injection detector, identity verifier, cryptographic approval system, or substitute for provider/repository controls. A clean result means only that this corpus and classifier found no indicator; it does not prove that content is safe or that a person approved an action.
