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

## Maven multi-module correction template

Use this only after a Maven failure that may involve internal modules, a private
mirror, or more than one Java lane. Record the following facts in the active
Work Item; do not invent values from a `pom.xml`.

1. Choose one build route: a single project-declared **reactor command**, or an
   explicitly declared module dependency order. Record the chosen command or
   ordered module list, its working directory, and why it is valid for this
   project. Do not run individual modules merely because their directories
   exist.
2. Before Maven runs, record the selected `settings.xml` path, whether the
   approved mirror is reachable, and whether the required private-repository
   access is available. Never paste credentials, tokens, passwords, or a private
   repository URL into the Work Item or a command transcript.
3. For every Java lane, record the required Java major and the actual `java`
   runtime selected for the Maven command. A lane with a different actual major
   is **blocked**; select the approved toolchain or correct the lane declaration
   before retrying.

If a required settings file, mirror, access grant, reactor command, dependency
order, or Java-major fact is missing, report `blocked` with that missing fact
and a recovery condition: obtain the project owner's approved configuration,
record it in the Work Item, then rerun the declared project command. This
template does not configure Maven, install a JDK, access a private repository,
or prove that an adopter build passed.

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## Need help?

Use the [project calibration guide](../calibration.md) for the questions the
Work Item will ask. If a fact is Unknown or a check stops, use
[installation troubleshooting](../../troubleshooting/installation.md). Keep
Unknown as Unknown; do not substitute a weaker check.
