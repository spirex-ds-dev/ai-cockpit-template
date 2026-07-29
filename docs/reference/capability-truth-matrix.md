---
author: Ray
title: "Capability Truth Matrix"
description: Evidence-backed distinction between implemented, template-only, adopter-installed, and planned AI Cockpit capabilities.
keywords:
  - ai-cockpit
  - capability-truth
  - evidence-governance
  - conditional-go
---
# Capability Truth Matrix

This matrix is the source of truth for public capability language during the Conditional GO remediation. The machine-readable record is [capability-truth-matrix.json](capability-truth-matrix.json); each row must use one of four statuses:

- `implemented`: verified in the repository by a command, source, and regression evidence.
- `template_only`: present in template code or documentation, but not proof of an adopter's installed capability.
- `adopter_installed`: produced and verified in an adopter repository; the evidence must name the installed runtime or fixture.
- `planned`: a remediation target without current evidence sufficient for an implemented claim.

## Current boundary

AI Cockpit is a Repository Governance Layer. It is not an Agent Runtime, Workflow Engine, Security Sandbox, identity system, or enterprise compliance control. The matrix therefore separates repository-local governance evidence from adopter-installed behavior and external release/security evidence.

## Reading rules

Documentation may claim a capability as current only when the corresponding matrix row is `implemented` or `adopter_installed` and its evidence paths are independently verifiable. `template_only` describes available template material, not a completed target-repository result. `planned` rows must remain visibly future work until their dedicated Work Item supplies commands, tests, and evidence.

The Quick Install archive-binding mechanism, bootstrap lifecycle, ten-stage calibration, Candidate activation, shared Calibration Inventory, and independent CI/Release Evidence are implemented in this repository. That status does not prove that the projected release is the provider's latest stable publication, that provider assets are public, or that a future candidate is available. Provider publication and availability require separate release evidence.

The byte-binding and release-truth correction is recorded in the [pre-release documentation truth corrective](../superpowers/plans/2026-07-29-pre-release-documentation-truth-corrective.md).

For exact row-level evidence, status vocabulary, and missing-evidence reasons, use the JSON source rather than inferring status from prose.

## Evidence binding

Every capability row is bound to `sourceEvidence`, `testEvidence`, `commandEvidence`, `limitations`, and an `evidenceSource` inventory containing each bound file's SHA-256 plus a canonical aggregate digest. The row `digest` binds that inventory and the row metadata. Missing files, duplicate aliases, escaping paths, symbolic links, changed bytes, or a mismatched row digest produce `evidence_stale`/validation failure; the row cannot support an implementation claim until it is regenerated and re-verified. A passing test, source-tree presence, or template installation alone is not proof that an adopter has the capability.

The WI-06 absurd corpus is intentionally negative and offline. L1 structural, L2 behavioral, L3 adversarial, and L4 recovery cases for unsupported world facts, forged evidence, impossible completion, unavailable APIs/toolchains, secrets, protected-branch writes, and production operations return `blocked`/`not_ready` with an explicit safe alternative. These cases demonstrate the repository boundary; they do not claim general hallucination prevention.

## Wizard boundary

The Installation Wizard is an implemented template entrypoint with an explicit confirmation-gated write boundary. The Calibration Wizard is an implemented presentation adapter over the persisted ten-stage Session; adopter execution, project-owned approval, and external toolchain results remain separate evidence. Fixture coverage for Swift, Kotlin/Android, and mixed monorepos demonstrates scenario modeling, not proof that every adopter's Xcode, Gradle, CocoaPods, JDK, or instrumented commands run successfully.
