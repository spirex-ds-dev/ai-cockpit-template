---
author: Ray
title: "WI08 Interactive Installer UX Design"
description: "Design for converging the existing installation wizard on the required ten-stage operator flow."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: wi-08-interactive-installer-ux
---

# WI08 Interactive Installer UX Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Decision

Extend the existing read-only detector, wizard plan, locale resources, and
`Installer` delegation. Do not introduce a second transaction engine or a
full-screen UI. The shell entrypoint already routes a no-argument TTY and
`--interactive` to the wizard, so it remains unchanged and is verified by
entrypoint tests.

## Ten-stage flow

The plan exposes exactly these stages:

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

Mode and profile are explicit operator selections. Standard is the displayed
profile default. Lite and Strict may be selected for planning, but the choice
does not create or activate a calibrated project profile. Calibration remains a
separate post-installation workflow.

## Data and write boundaries

`ai_installer_detection` remains the repository-fact authority.
`ai_install_plan` turns those facts, the selected mode/profile, and a read-only
action preview into the ten immutable stages. `ai_install_wizard` owns prompts,
localized rendering, stop decisions, and result presentation. Only
`install_ai_cockpit.Installer` may write.

Before affirmative confirmation, the wizard may read repository facts and
construct a dry-run action preview. It must not acquire the installer lock,
create or switch branches, or modify the target. Dry Run, blocked readiness,
unresolved conflicts, and declined confirmation return without invoking a write
Installer.

## Planned changes and conflicts

The preview classifies Installer actions as add, modify, or skip and reports
whether product source code changes are expected. Paths under AI Cockpit's
managed governance surface are not product source changes. Conflict Review
shows detected repository conflicts and the Installer's managed-conflict
boundary before confirmation.

## Results

After delegation, Verification reports the Installer exit code and whether the
transaction completed. Next Action directs a successful adoption to review the
generated Work Item and run calibration separately. Failure output states that
the Installer rollback boundary was invoked; it does not claim recovery beyond
the transaction's observable result.

The wizard never commits, pushes, creates a PR, merges, deletes a successful
installation branch, activates Strict, or reports installation as completed
calibration.

## Verification

Focused tests cover stage order, profile default and explicit selection,
localized key parity, preview counts, conflict and readiness stops, no-write
Dry Run and cancellation, Installer delegation, success/failure result chrome,
and shell entrypoint compatibility. Existing Installer rollback and adoption
end-to-end tests remain the executable evidence for filesystem and Git-head
restoration.
