---
author: Ray
title: "Interactive Installation Wizard"
description: "The ten-stage, read-only-until-confirmed installation flow."
audience:
  - maintainer
  - auditor
status: current
authority: supporting
lastVerifiedBy: capability-truth-matrix
---

# Interactive Installation Wizard

`scripts/ai_install_wizard.py` orchestrates ten fixed stages over the read-only
facts from `ai_installer_detection.py` and a dry-run action preview:

1. Target Repository
2. Readiness
3. Installation Mode
4. Governance Profile
5. Planned Changes
6. Conflict Review
7. Explicit Confirmation
8. Installation
9. Verification
10. Next Action

`ai_installer_evidence.summarize_installation_actions()` classifies the dry-run
Installer actions into add, modify, and skip counts and flags any path outside
the known governance installation surface as a product-source change. The plan
also identifies the adoption or upgrade branch.

The governance profile is a plan-only choice with Standard as the display
default. Selecting Lite or Strict does not create or activate a calibrated
project profile. Calibration and production readiness remain separate Work
Items and evidence boundaries.

Before affirmative confirmation, the target remains read-only. Dry Run,
blocked readiness, conflict blockers, cancellation, EOF, and interruption do
not invoke a write Installer. After confirmation, the wizard constructs the
existing `install_ai_cockpit.Installer`; it does not duplicate transaction,
conflict, backup, Git-head restoration, or filesystem rollback behavior.

The wizard never commits, pushes, creates a PR, merges, deletes the successful
installation branch, or activates Strict policy. Verification reports the
Installer exit code. A failure names the Installer rollback boundary but does
not overclaim that recovery succeeded without inspecting the target state.

The executable accepts `--language ja|en|zh-CN` and otherwise uses shared locale
resolution. Selection labels, ten-stage headings, confirmation, STOP,
verification, and next-action chrome come from exact-parity resources. Detected
paths, commands, values, and evidence remain verbatim rather than being machine
translated.
