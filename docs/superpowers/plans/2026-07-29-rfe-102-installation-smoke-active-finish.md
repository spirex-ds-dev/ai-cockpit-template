---
author: Ray
title: "RFE-102 Installation Smoke Explicit Archive Repair"
description: "Repair the installed-adopter smoke lifecycle so active Outcome reporting is followed by explicit archive before commit and post-install guards."
---

# RFE-102: installation smoke explicit archive repair

## Problem

PR #462 changed `ai-finish` to retain an active Outcome. The installed-adopter
smoke fixture still committed immediately after finish, so its active Contract
compared the installation baseline to the pre-install commit and the coverage
guard correctly blocked the resulting untested Runtime diff.

## Plan

1. Insert explicit archive after the active Outcome and before the install
   commit in installation smoke.
2. Add a static workflow regression for that ordering.
3. Run focused workflow tests and the required governed checks.
4. Rerun hosted installation smoke and record the result.

## Acceptance mapping

- Explicit archive before commit: `.github/workflows/smoke.yml`.
- Regression: `tests/test_quality_gate_architecture.py`.
- Hosted proof: PR #462 installation-smoke.
