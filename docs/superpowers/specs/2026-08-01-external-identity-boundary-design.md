---
author: Ray
title: "WI09 External Identity Boundary Design"
description: "Design for separating repository-recorded approval from external identity evidence."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: wi-09-external-identity-boundary
---

# External Identity Boundary Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Goal

Separate repository-local approval statements from provider- or
enterprise-bound identity evidence, and fail closed when destructive changes
rely only on a local actor name.

## Design

- Add one strict Trust Layer Approval Evidence schema with four identity levels.
- Add a deterministic semantic validator for level-specific evidence and an
  honest display state, `repository_recorded_only`.
- Require the new identity evidence inside destructive Contract approval
  records while preserving ordinary restricted-write records.
- Reuse `check-trust-schemas`; do not add a top-level Gate or contact external
  services.

## Boundaries

Provider and enterprise identifiers are supplied evidence, not independently
authenticated facts. The validator checks completeness, level, and scope; the
provider or enterprise system remains the evidence producer.
