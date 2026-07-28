---
author: Ray
title: "WI-10 Prompt-First Multiplatform Installation Design"
description: Design for a beginner-safe trilingual installation path with governed prompts and platform examples.
keywords:
  - installation
  - prompt-first
  - beginner
  - ios
  - android
  - java
  - multilingual
---

# WI-10 Prompt-First Multiplatform Installation Design

## Problem

The current WI-10 pages are fact-rich but are not yet an adoption path for a
person with no programming experience. Chinese has no complete
`installation.zh-CN.md`, the main path is command-heavy, iOS/Android/Java
walkthroughs are absent, and the scaffold, calibration, first PR, recovery,
and final-success sequence still requires the reader to infer steps.

Installation is the product's adoption gateway. A completion claim is invalid
if a reader can reach a command, choice, failure, or human decision without
knowing what it means and what to do next.

## Design principles

1. **Prompt-first, not authority-first.** Copy-ready prompts ask the agent to
   inspect read-only, explain findings, expose unknowns, propose a plan, and
   stop for confirmation before writes.
2. **Every action has a checkpoint.** Each step states the action, expected
   visible result, stop condition, and recovery action.
3. **Commands are exceptional.** A command remains only for human bootstrap or
   direct evidence inspection. It must carry a command-evidence label and a
   plain-language purpose, success signal, and failure response.
4. **Complete language paths.** English, Simplified Chinese, and Japanese use
   the same section IDs, order, safety meaning, and platform coverage. A
   translation may not become a summary.
5. **Evidence before platform claims.** Detecting an Xcode, Gradle, Maven, or
   Java project does not prove that the toolchain, simulator/device, signing,
   credentials, or hosted CI works.
6. **Capability truth stays external.** Documentation teaches the governed
   procedure; it does not promote a planned or template-only capability.

## Information architecture

The complete installation guides are:

- `docs/getting-started/installation.md`
- `docs/getting-started/installation.zh-CN.md`
- `docs/getting-started/installation.ja.md`

Each guide contains these machine-checked novice stages in this order:

1. `before-you-start`
2. `open-your-project`
3. `copy-discovery-prompt`
4. `review-read-only-report`
5. `choose-wizard-options`
6. `review-installation-plan`
7. `approve-scaffold-write`
8. `inspect-scaffold`
9. `complete-calibration`
10. `run-local-checks`
11. `complete-first-work-item`
12. `review-pr-and-hosted-ci`
13. `merge-and-close`
14. `recover-from-a-stop`
15. `confirm-installation-success`

The complete platform guides are nine focused documents under
`docs/getting-started/examples/`: iOS, Android, and Java in all three
languages. Every platform guide uses the same platform stages:

1. `detect-project`
2. `collect-toolchain-evidence`
3. `choose-stack-and-boundaries`
4. `discover-quality-commands`
5. `calibrate-generated-and-critical-paths`
6. `stop-and-recover`
7. `verify-platform-adoption`

The `30-second-start` pages remain short entrypoints. They present the first
copy-ready prompt and link to the complete same-language installation guide.
The standard adoption guides summarize the lifecycle and link back to the
same-language complete procedure. READMEs provide only a short entry.

## Prompt contract

An authoritative installation prompt must require the agent to:

- make no repository changes during discovery;
- identify the repository remote and default branch instead of assuming
  `origin/main`;
- report dirty worktree state, missing initial commit, missing tools, and
  unknown project facts;
- explain technical terms in plain language;
- distinguish observed evidence, inference, and unknown;
- list the exact files it proposes to create or change;
- stop and ask the human to approve the plan before writes;
- never commit, push, create or merge a PR, publish, delete, or invent a
  project command;
- preserve unrelated user changes.

Later prompts may request a single governed phase, but must preserve the same
boundaries. Human confirmation of one phase does not authorize later phases.

## Scaffold walkthrough

The guides explain what the installation scaffold contributes, without
claiming that file creation completes adoption:

- agent operating rules and glossary;
- active Work Item Contract and Summary locations;
- policy, guard, trust, and schema files;
- scripts and Make targets;
- stack preset and optional examples;
- current Cockpit Status and generated evidence;
- adopter-owned calibration configuration;
- CI workflow or integration instructions.

After the write, the agent must produce a changed-file inventory grouped by
category, explain conflicts or preserved files, and run the installer-owned
validation before calibration begins.

## Calibration walkthrough

The hand sequence explains every executable stage:

1. repository role;
2. language and stack;
3. source boundaries;
4. test boundaries;
5. generated artifacts;
6. critical paths;
7. quality commands;
8. review requirements (`review_requirements`);
9. risks and unknowns;
10. adoption readiness.

For every stage, the guide explains the question, evidence to inspect, example
answer, and the four answer forms: yes/no, alternative input, unknown, and
not-applicable with a reason. Unknown stays unknown. The agent may prepare a
candidate; only the human reviews and confirms it.

## First governed lifecycle

The guide does not end after installation. It first completes the dedicated
`adopt_ai_cockpit` Work Item through local gates, finish/archive,
archive-evidence commit, push, PR, hosted CI, human review, merge, lifecycle
closure, branch deletion, and base synchronization. Only then does a separate
`configure_ai_cockpit` Work Item perform Calibration and complete the same
independent lifecycle. It separates actions the agent may prepare from
decisions the human must make.

## Platform boundaries

### iOS

Discovery may identify `.xcodeproj`, `.xcworkspace`, `Package.swift`,
`Podfile`, schemes, test targets, and generated directories. The guide does
not assume Xcode, CocoaPods, signing, simulator availability, or a working
scheme. Commands are accepted only after repository or human evidence.

### Android

Discovery may identify `gradlew`, settings files, modules, flavors, variants,
local and instrumented tests, and generated build directories. The guide does
not assume a JDK, Android SDK, emulator/device, credentials, or a specific
variant. Unit and device tests remain distinct evidence.

### Java

Discovery may identify Maven or Gradle wrappers, modules, JDK configuration,
test frameworks, coverage, and generated outputs. The guide does not assume a
system Maven/Gradle installation, JDK version, integration service, or a
single-module layout.

## Executable anti-omission checks

`scripts/check_docs_metadata.py` will add:

- exact trilingual installation-file and section parity checks;
- required prompt and prompt-safety marker checks;
- required novice-stage and ten-stage calibration checks;
- required nine platform documents, platform-stage parity, and non-claim
  boundary checks;
- same-language README/layer link checks;
- retained-command explanation-marker checks.

`tests/test_docs_metadata.py` will mutate one requirement at a time and prove
the gate fails. The positive repository check must pass only when the complete
instruction-plan-implementation-acceptance chain is present.

## Decision

Implement the complete prompt-first route in this corrective Work Item. Do not
shorten the Chinese or Japanese guides, hide the lifecycle behind links, or
expand scope into runtime/installer changes.
