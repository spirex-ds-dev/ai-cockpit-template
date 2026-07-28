---
author: Ray
title: "Android Installation Example"
description: Beginner-safe AI Cockpit calibration example for Android repositories.
keywords: [ai-cockpit, android, gradle, installation]
---

# Android Installation Example

Complete [Installation](../installation.md) Steps 1–4. Use platform Stages
1–4 during Installation Steps 5–6, return to Steps 7–8 for write/Adoption
closure, use Stage 5 during Calibration, Stage 6 when blocked, and Stage 7
after Installation Step 13. This page does not replace the lifecycle.

| Main Installation | Use on this page | Then return to |
| --- | --- | --- |
| Steps 1–4 | Nothing; finish discovery | Step 5 |
| Steps 5–6 | Copy rows 1–4, one at a time | Step 7 |
| Steps 7–8 | Nothing; finish write/Adoption closure | Step 9 |
| Step 9 | Copy row 5 | Step 10 |
| Any STOP | Copy row 6 | Same blocked step |
| After Step 13 | Copy row 7 once | Steps 14/15 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## Copy this Android prompt

```text
Guide Android Stages 1–4, 6, and 7 read-only, one at a time. At Stage 5,
propose a Candidate diff without writing; the main Installation Step 9 owns
any separate write approval. Define Gradle,
module, flavor, variant, JDK, SDK, unit test, and device test in plain language.
For each stage show evidence found, plain meaning, recommended value, what is
unproven, expected result, and STOP/escalation. Never invent a Gradle task or
claim a JDK, Android SDK, emulator/device, signing key, secret, or hosted run.
Wait for my answer after each stage and change nothing.
```

Example: finding `gradlew` means the project supplies a Gradle Wrapper; it does
not prove the required JDK/Android SDK is installed. Recommend `android` only
after module evidence is clear; stop for the Android owner on an unknown variant.

Copy one row at a time:

<!-- platform-step-table: copy-request,example,pass,stop -->
| Stage | Exact request | Example result and choice | PASS | STOP/contact |
| --- | --- | --- | --- | --- |
| 1 Detect | “List Wrapper/settings/build/catalog files, every module, flavor, build type, variant, tests, manifests, generated paths, and CI. Change nothing.” | `gradlew` exists, but the app module name remains evidence-dependent. | Modules and test locations are mapped. | Module/variant Unknown; Android owner. |
| 2 Toolchain | “Show evidence for Wrapper, AGP, Kotlin, JDK, SDK levels, emulator/device, signing, credentials, and CI image.” | Wrapper exists; required JDK/SDK availability is separately checked. | Required versions/environments are evidenced. | JDK/SDK/device/secret missing; Android/CI owner. |
| 3 Boundaries | “Propose `android` or `generic`; map each module’s maintained source/tests and excluded cache/build/generated paths.” | Mixed monorepo may require `generic` until mapping is complete. | Every module boundary has evidence. | Unowned module/generated path; module owner. |
| 4 Commands | “Copy exact Wrapper tasks from files/CI; explain module, flavor, build type, variant, prerequisites, success, and failure.” | Unit, lint, device, and release tasks remain separate evidence. | Exact required tasks are evidenced. | Invented task or unknown variant; Android/CI owner. |
<!-- platform-stage5: proposal-only -->
| 5 Calibrate | “Propose Candidate entries for generation, manifests, R8, migrations, signing, bundles, permissions, privacy/security, and reviewers. Do not write or activate.” | Release signing requires a release reviewer. | Proposed diff includes high-risk/generated paths. | Ownership or generator missing; build/release owner. |
| 6 Recover | “Keep failure output, resolve the exact JDK/SDK/device/secret/generated-drift cause, and rerun the same Wrapper task.” | A unit test cannot replace required device evidence. | Same task later passes. | Weaker substitute proposed; stop. |
| 7 Verify | “Map ten calibration stages, variant-specific local/hosted results, PR Head SHA, human merge, closure, and branch deletion.” | Hosted smoke is not this adopter’s variant proof. | All evidence matches this repository/commit. | Any missing platform/lifecycle evidence; repository owner. |

The sections below only explain the table rows; do not execute them again.
<!-- platform-stage: detect-project -->
## 1. Detect the project

Read-only discovery lists `gradlew`, settings/build/version-catalog files,
modules, product flavors, build types, unit tests, `androidTest`, manifests,
generated directories, and CI. Never assume the app module is named `app`.

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Collect toolchain evidence

Record Wrapper/AGP/Kotlin/JDK declarations, SDK levels, variants, emulator or
device needs, signing, credentials, and CI images. A Gradle Wrapper does not
prove the required JDK, Android SDK, emulator/device, secrets, or hosted CI.

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Choose stack and boundaries

Use `android` for a verified Android layout; use `generic` for unusual mixed
monorepos until module boundaries are calibrated. Map every module's
`src/main`, `src/test`, and `src/androidTest`; exclude `.gradle`, `build`, SDK,
and generated output according to project evidence.

<!-- platform-stage: discover-quality-commands -->
## 4. Discover quality commands

Use Wrapper tasks evidenced by files or CI. Identify the exact module, flavor,
build type, and variant. Unit tests, lint, instrumented/device tests, and
release builds are different evidence. Do not invent task names.

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Calibrate generated and critical paths

Propose Candidate entries for resource/code generation, manifests, ProGuard/R8, migrations, signing,
release bundles, permissions, privacy/security configuration, and reviewer
ownership.

<!-- platform-stage: stop-and-recover -->
## 6. Stop and recover

Stop on JDK/SDK mismatch, unknown variant, unavailable device, missing secret,
daemon/cache ambiguity, or generated drift. Gather evidence and rerun the same
Wrapper task; never substitute a cheaper task as a pass.

<!-- platform-stage: verify-platform-adoption -->
## 7. Verify Android adoption

Require all calibration stages, variant-specific command evidence, separate
unit/device and local/hosted results, reviewed PR, and lifecycle closure.
