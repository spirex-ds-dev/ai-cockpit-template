---
author: Ray
title: "iOS Calibration Start"
description: Simple Work Item-first start for an iOS project after AI Cockpit installation.
keywords: [ai-cockpit, ios, xcode, swift, calibration]
---

# Start iOS calibration

Use this page after AI Cockpit is installed. You do not need to understand
Xcode, signing, schemes, or calibration internals before starting.

<!-- platform-entry: work-item-first -->
## Copy this once

```text
This is an iOS project. Create a calibration Work Item plan, but do not change
files yet. Read the repository and tell me in plain language: what kind of iOS
project it is, what you found, what is Unknown, and what you need me to confirm.
Do not guess Xcode, scheme, simulator, signing, device, command, or CI facts.
Wait for my approval before writing anything.
```

## What happens next

The agent creates a reviewable calibration Work Item. You review its plan, then
approve only the proposed changes. A project file or workspace alone does not
prove that Xcode, a scheme, a simulator, signing, or hosted macOS CI is ready.

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## Need help?

Use the [project calibration guide](../calibration.md) for the questions the
Work Item will ask. If a fact is Unknown or a check stops, use
[installation troubleshooting](../../troubleshooting/installation.md). Keep
Unknown as Unknown; do not substitute a weaker check.
