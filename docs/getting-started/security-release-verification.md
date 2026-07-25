---
author: Ray
title: "Security and Release Verification"
description: "The evidence boundary for security, supply chain, version, and release decisions."
keywords:
  - security
  - release
  - supply-chain
  - verification
---

# Security and Release Verification

Release and security claims require current, source-bound evidence. Local syntax checks and fixture runs are useful but do not substitute for hosted checks, release assets, signatures, provenance, or an adopter's own controls.

Use `syntax_tested` for documentation-only command checks, `fixture_executed` for controlled local evidence, `hosted_executed` for CI evidence, and `adopter_required` where the target project must independently verify behavior. A missing or stale release/version/capability binding is a stop condition, not a green result.

The published distribution flow remains the authority for tag, archive, installer, SBOM, provenance, and release-asset verification. This page does not publish a version or assert Japanese capability; the comprehensive Japanese assessment is a prerequisite Work Item before publication.
