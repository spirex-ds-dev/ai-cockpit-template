---
author: Ray
title: "Java Installation Example"
description: Beginner-safe AI Cockpit calibration example for Java repositories.
keywords: [ai-cockpit, java, maven, gradle, installation]
---

# Java Installation Example

Complete [Installation](../installation.md) Steps 1–4 first. Do not run this
page from top to bottom. If you are at main Steps 5–6, copy rows 1–4 below one
at a time, then return to main Step 7. At any other point, use only the row
that matches your current step in the table below.

Copy the setup prompt below once; it only establishes how the agent will guide
you. After its response, execute only one row at a time from the **Primary
action table**. The later filled-answer table is an example, not a second
sequence to copy.

Table terms: proof (**evidence**), accountable person (**owner**), checking
person (**reviewer**), release identity (**signing**), settings file
(**manifest**), test data (**fixture**), and complete end-of-work processing
(**closure**). The agent must show both the formal term and plain meaning.

| Main Installation | Use on this page | Then return to |
| --- | --- | --- |
| Steps 1–4 | Nothing; finish discovery | Step 5 |
| Steps 5–6 | Copy rows 1–4, one at a time | Step 7 |
| Steps 7–8 | Nothing; finish write/Adoption closure | Step 9 |
| Step 9 | Use row 5 inside Calibration | Return to and complete the rest of Step 9, then Step 10 |
| A STOP produced by platform rows 1–5 | Copy row 6 | Same blocked platform stage |
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
Do not begin Stage 1 now; wait for me to paste the first Primary action table
row. After every later stage, wait for my answer and change nothing.
```

Example: finding `pom.xml` means the project describes a Maven build; it does
not prove Maven, the required JDK, or integration services work. Recommend
`java` after modules are mapped; stop for the Java owner on an unknown profile.

### Primary action table

Copy one row at a time:

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| Stage | Exact request | Example result and choice | PASS | STOP/contact |
| --- | --- | --- | --- | --- |
| 1 Detect | “List Maven/Gradle wrappers/manifests, modules, toolchains, JDK declarations, source/test sets, plugins, coverage, generated source, packaging, and CI.” | `pom.xml` describes Maven; it does not prove one module or a working tool. | Modules/build family are mapped. | Module/build layout Unknown; Java owner. |
| 2 Toolchain | “Show evidence for wrapper, JDK/vendor, mirrors, services, credentials, network, and hosted image.” | A JDK declaration states a requirement, not local availability. | All required environments have evidence. | JDK/service/credential/network Unknown; Java/CI owner. |
| 3 Boundaries | “Propose `java` or `generic`; list maintained source/test/resources and excluded target/build/cache/generated/vendor paths.” | Mixed monorepo stays `generic` until modules are mapped. | Every path has evidence/owner. | Generated/source ownership unclear; module owner. |
| 4 Commands | “Copy exact wrapper lifecycle/tasks from files/CI and explain profile, module, filters, services, coverage, prerequisites, success, and failure.” | Compile, unit, integration, package, and publish are different evidence. | Exact required commands are evidenced. | Invented command/profile or missing service; Java/build owner. |
| 5 Calibrate | “Propose Candidate entries for annotation/schema/client generation, migrations, dependency catalogs, signing/publishing, security/release paths, and reviewers. Do not write or activate.” | Publishing requires release ownership beyond unit tests. | Proposed diff includes generators and critical paths. | Generator/reviewer missing; build/release owner. |
| 6 Recover | “Preserve output, resolve the exact JDK/module/profile/service/network/generated-drift cause, and rerun the same command.” | Unit tests cannot replace required integration evidence. | Same command later passes. | Reject the weaker substitute, STOP, and contact the owner named in the blocked stage; rerun that stage after evidence arrives. |
| 7 Verify | “Show an evidence table with one row per requirement and columns for module/profile, evidence path or URL, commit SHA, PASS/STOP, and missing item; include ten stages, local/hosted results, PR Head SHA, human merge, closure, and branch deletion.” | Template fixture evidence is not adopter proof. | All rows match repository/commit and none is missing. | Missing platform/lifecycle evidence; repository owner. |

<!-- platform-filled-example: seven-stages -->
### Filled-answer example: fictional `SampleOrders`

Each row is independent. A STOP row does not continue. Obtain the owner's
answer, rerun the same stage, and continue only after PASS. Later rows show the
display after an earlier STOP has been resolved.

| Stage | Example agent answer | User answer to copy | Success display | Information to provide when stopped |
| --- | --- | --- | --- | --- |
| 1 | “Found Maven Wrapper, `api`/`service` modules, and unit/integration tests.” | `List every module and test type as candidates.` | Module, build, and test inventory. | Give `pom.xml` paths to the Java owner. |
| 2 | “Toolchain is Temurin JDK 21; integration database is unconfirmed.” | `Keep the database Unknown and STOP.` | Source lines for JDK and services. | Give toolchain/service facts to Java/CI owners. |
| 3 | “`src/main` is maintained and `target/` is output; propose java preset.” | `I accept the evidenced boundaries.` | Included/excluded paths per module. | Give unknown ownership to the module owner. |
| 4 | “CI has the Wrapper unit command; integration profile is unconfirmed.” | `Record only unit and STOP with integration Unknown. Ask the build owner and rerun Stage 4; use not applicable only with evidence that integration testing is not required.` | Exact command, source, and success condition. | Give profile/service facts to the build owner. |
| 5 | “Schema generation, migration, and publishing are critical.” | `Propose only a reviewer-bound Candidate diff; do not write or activate.` | Proposed generator, paths, and reviewers. | Give ownerless items to the release owner. |
| 6 | “Integration failed to connect to the database.” | `Preserve the log, provide the same service, and rerun the same integration command.` | The same command succeeds. | Give the log, profile, and service to the owner. |
| 7 | “Checked module/profile CI, PR Head SHA, merge, closure, and branch deletion.” | `List every link and mark Java adoption PASS only if none is missing.` | All evidence binds to the same commit. | Give missing items and the PR URL to the repository owner. |

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
