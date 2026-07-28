---
author: Ray
title: "Java Installation Example"
description: Beginner-safe AI Cockpit calibration example for Java repositories.
keywords: [ai-cockpit, java, maven, gradle, installation]
---

# Java Installation Example

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
## Copy this Java prompt

```text
Guide Java Stages 1–4, 6, and 7 read-only, one at a time. At Stage 5, propose
a Candidate diff without writing; the main Installation Step 9 owns any
separate write approval. Define Maven, Gradle,
Wrapper, module, JDK, profile, unit test, and integration test in plain
language. For each stage show evidence, plain meaning, recommended value,
what remains unproven, expected result, and STOP/escalation. Never invent a
command or claim a JDK, build tool, service, credential, network, or hosted run.
Wait for my answer after every stage and change nothing.
```

Example: finding `pom.xml` means the project describes a Maven build; it does
not prove Maven, the required JDK, or integration services work. Recommend
`java` after modules are mapped; stop for the Java owner on an unknown profile.

Copy one row at a time:

<!-- platform-step-table: copy-request,example,pass,stop -->
| Stage | Exact request | Example result and choice | PASS | STOP/contact |
| --- | --- | --- | --- | --- |
| 1 Detect | “List Maven/Gradle wrappers/manifests, modules, toolchains, JDK declarations, source/test sets, plugins, coverage, generated source, packaging, and CI.” | `pom.xml` describes Maven; it does not prove one module or a working tool. | Modules/build family are mapped. | Module/build layout Unknown; Java owner. |
| 2 Toolchain | “Show evidence for wrapper, JDK/vendor, mirrors, services, credentials, network, and hosted image.” | A JDK declaration states a requirement, not local availability. | All required environments have evidence. | JDK/service/credential/network Unknown; Java/CI owner. |
| 3 Boundaries | “Propose `java` or `generic`; list maintained source/test/resources and excluded target/build/cache/generated/vendor paths.” | Mixed monorepo stays `generic` until modules are mapped. | Every path has evidence/owner. | Generated/source ownership unclear; module owner. |
| 4 Commands | “Copy exact wrapper lifecycle/tasks from files/CI and explain profile, module, filters, services, coverage, prerequisites, success, and failure.” | Compile, unit, integration, package, and publish are different evidence. | Exact required commands are evidenced. | Invented command/profile or missing service; Java/build owner. |
<!-- platform-stage5: proposal-only -->
| 5 Calibrate | “Propose Candidate entries for annotation/schema/client generation, migrations, dependency catalogs, signing/publishing, security/release paths, and reviewers. Do not write.” | Publishing requires release ownership beyond unit tests. | Proposed diff includes generators and critical paths. | Generator/reviewer missing; build/release owner. |
| 6 Recover | “Preserve output, resolve the exact JDK/module/profile/service/network/generated-drift cause, and rerun the same command.” | Unit tests cannot replace required integration evidence. | Same command later passes. | Weaker substitute proposed; stop. |
| 7 Verify | “Map ten calibration stages, module/profile-specific local/hosted results, PR Head SHA, human merge, closure, and branch deletion.” | Template fixture evidence is not adopter proof. | All evidence matches repository/commit. | Missing platform/lifecycle evidence; repository owner. |

The sections below only explain the table rows; do not execute them again.
<!-- platform-stage: detect-project -->
## 1. Detect the project

Read-only discovery lists Maven/Gradle wrappers and manifests, modules,
toolchains, JDK declarations, source/test sets, integration-test plugins,
coverage, generated sources, packaging, and CI. Do not assume one module.

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Collect toolchain evidence

Record the wrapper, required JDK/vendor, repository mirrors, services,
credentials, and hosted image. A `pom.xml` or Gradle file does not prove Maven,
Gradle, the correct JDK, network services, secrets, or hosted CI is available.

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Choose stack and boundaries

Use `java` when the Java layout is verified; use `generic` for mixed monorepos
until modules are mapped. Identify maintained source/test resources and
exclude target/build/cache/generated/vendor paths according to evidence.

<!-- platform-stage: discover-quality-commands -->
## 4. Discover quality commands

Prefer project wrappers and copy lifecycle/tasks from files or CI. Explain
profiles, modules, test filters, integration services, and coverage output.
Compile, unit, integration, static analysis, packaging, and publication are
different evidence. Never invent a command.

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Calibrate generated and critical paths

Propose Candidate entries for annotation/code generation, schema/client generation, migrations,
dependency locks/catalogs, signing/publishing, security configuration, release
automation, and reviewer ownership.

<!-- platform-stage: stop-and-recover -->
## 6. Stop and recover

Stop on JDK mismatch, unresolved module/profile, missing service/credential,
network-only dependency, or generated drift. Gather owner/CI evidence and
rerun the same command; do not replace integration evidence with unit tests.

<!-- platform-stage: verify-platform-adoption -->
## 7. Verify Java adoption

Require all calibration stages, module/profile-specific commands, separate
local/hosted evidence, reviewed PR, and lifecycle closure.
