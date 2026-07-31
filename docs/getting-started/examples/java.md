---
author: Ray
title: "Java Calibration Start"
description: Simple Work Item-first start for a Java project after AI Cockpit installation.
keywords: [ai-cockpit, java, maven, gradle, calibration]
---

# Start Java calibration

Use this page after AI Cockpit is installed. You do not need to understand JDKs,
Maven, Gradle, modules, services, or calibration internals before starting.

<!-- platform-entry: work-item-first -->
## Copy this once

```text
This is a Java project. Create a calibration Work Item plan, but do not change
files yet. Read the repository and tell me in plain language: what kind of Java
project it is, what you found, what is Unknown, and what you need me to confirm.
Do not guess JDK, build tool, module, profile, service, credential, command, or
CI facts. Wait for my approval before writing anything.
```

## What happens next

The agent creates a reviewable calibration Work Item. You review its plan, then
approve only the proposed changes. A Maven or Gradle file alone does not prove
that the JDK, wrapper, service, credentials, or hosted CI is ready.

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## Need help?

Use the [project calibration guide](../calibration.md) for the questions the
Work Item will ask. If a fact is Unknown or a check stops, use
[installation troubleshooting](../../troubleshooting/installation.md). Keep
Unknown as Unknown; do not substitute a weaker check.
