---
author: Ray
title: "Strict Installation and Supply-Chain Verification"
description: "The security-owner route for verifying an AI Cockpit installation release."
---

# Strict Installation and Supply-Chain Verification

Use this route when you own release approval, a private mirror, or supply-chain
evidence. It is not required reading before the simple installation path.

Verify the dynamically resolved release, its tag-pinned metadata and source
commit, the installer and archive assets, and their SHA-256 digests. Do not
silently fall back to an older release or a moving branch. A Release owner must
review any exception before the evidence is checked again.

The complete evidence rules, private-mirror boundary, and enterprise limits are
in [Security and Release Verification](security-release-verification.md).
