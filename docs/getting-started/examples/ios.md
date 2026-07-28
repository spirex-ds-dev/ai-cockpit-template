---
author: Ray
title: "iOS Installation Example"
description: Beginner-safe AI Cockpit calibration example for iOS repositories.
keywords: [ai-cockpit, ios, xcode, swift, installation]
---

# iOS Installation Example

Complete [Installation](../installation.md) Steps 1–4. Use platform Stages
1–4 below while reviewing Installation Steps 5–6; return to Installation
Steps 7–8 for the write and Adoption closure; use platform Stage 5 during
Calibration; Stage 6 whenever blocked; and Stage 7 after Installation Step 13.
This page never replaces the main lifecycle.

| Main Installation | Use on this page | Then return to |
| --- | --- | --- |
| Steps 1–4 | Nothing; finish discovery first | Installation Step 5 |
| Steps 5–6 | Copy table rows 1–4, one at a time | Installation Step 7 |
| Steps 7–8 | Nothing; complete write and Adoption closure | Installation Step 9 |
| Step 9 | Copy table row 5 | Installation Step 10 |
| Any STOP | Copy table row 6 | The same blocked main step |
| After Step 13 | Copy table row 7 once | Installation Step 14/15 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## Copy this iOS prompt

```text
Guide iOS Stages 1–4, 6, and 7 read-only and one at a time. At Stage 5,
propose a Candidate diff but do not write it; the main Installation Step 9
owns any separately approved Candidate write. Define
every Xcode/Swift term. For each stage return: evidence found, plain meaning,
recommended Wizard/Calibration value, what remains unproven, expected result,
and STOP/escalation condition. Do not invent xcodebuild, scheme, destination,
signing, simulator, CocoaPods, or hosted-CI facts. Wait for my answer after
every stage and make no changes.
```

Example: finding `MyApp.xcworkspace` means “an Xcode workspace exists”; it does
not mean Xcode or a working scheme exists. Recommendation: start from the
`swift` preset, then calibrate project-specific commands; stop for the iOS
owner if scheme/destination evidence is missing.

Copy one row at a time:

<!-- platform-step-table: copy-request,example,pass,stop -->
| Stage | Exact request | Example result and choice | PASS | STOP/contact |
| --- | --- | --- | --- | --- |
| 1 Detect | “List `.xcodeproj`, `.xcworkspace`, `Package.swift`, dependency files, app/extensions, schemes, tests, and CI. Change nothing.” | `MyApp.xcworkspace` exists; classify as workspace, not proof of a runnable app. | Layout and owners are clear. | Mixed/unknown layout; iOS owner. |
| 2 Toolchain | “Show project/CI evidence for Xcode/Swift versions, dependency manager, scheme, destination, signing, simulator/device, and hosted macOS.” | CI pins Xcode 16; local availability remains separately Unknown. | Every required tool/environment has evidence. | Missing version, scheme, destination, signing, or host; iOS/release owner. |
| 3 Boundaries | “Propose `swift` or `generic`, maintained source, generated/vendor/output exclusions, and evidence for each.” | `swift` is a starting preset; non-SPM commands still need calibration. | Each inclusion/exclusion is explained. | Preset would hide mixed layout; module owner. |
| 4 Commands | “Copy exact repository/CI commands and explain scheme, destination, configuration, prerequisite, success, and failure. Do not invent.” | An evidenced test command is separate from archive/signing. | Commands and environments are evidenced. | Missing command or secret/device; iOS/CI owner. |
<!-- platform-stage5: proposal-only -->
| 5 Calibrate | “Propose Candidate entries for generators, entitlements, privacy manifest, signing, archive/release, migrations, deployment, and reviewers. Do not write or activate.” | Signing paths require a release reviewer. | Proposed diff shows all critical/generated paths. | Owner or regeneration rule missing; build/release owner. |
| 6 Recover | “Preserve the failure evidence, name the missing fact and owner, update the Candidate only after evidence arrives, and rerun the same check.” | Unknown destination stays blocking. | Same requirement later passes. | Suggested weaker substitute; stop and escalate. |
| 7 Verify | “Map all ten calibration stages, local/hosted results, PR Head SHA, human merge, closure, and branch deletion. Report incomplete if one is absent.” | A minimal SPM fixture is not adopter Xcode evidence. | All evidence belongs to this repository and commit. | Any missing lifecycle/platform evidence; repository owner. |

The sections below are read-only explanations for the seven table rows. Do not
run them as a second sequence.
<!-- platform-stage: detect-project -->
## 1. Detect the project

Ask the agent read-only to list `.xcodeproj`, `.xcworkspace`, `Package.swift`,
`Podfile`, `Cartfile`, schemes, app/extensions, unit/UI test targets, and CI
files. It must distinguish an SPM-only package from an Xcode app/workspace.

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Collect toolchain evidence

Record the Xcode/Swift version declared by project and CI files, dependency
manager, selected schemes, signing needs, and simulator/device requirements.
An existing Xcode file does not prove Xcode, CocoaPods, a simulator, signing
identity, or hosted macOS CI is available. Unknown remains blocking.

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Choose stack and boundaries

Use `swift` as the preset starting point for Swift/Xcode layouts, but replace
SPM defaults through mandatory project calibration for non-SPM projects. Use
`generic` only when mixed repository evidence makes the Swift preset misleading.
Source usually includes app/framework source; exclude DerivedData, `.build`,
Pods, generated code, and checked-in vendor content unless the project proves
another ownership rule.

<!-- platform-stage: discover-quality-commands -->
## 4. Discover quality commands

Ask the agent to copy commands from the repository or hosted workflow and
explain scheme, destination, configuration, and prerequisites. Do not invent
`xcodebuild` or `pod` commands. Keep unit, UI/device, archive, and signing
evidence separate.

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Calibrate generated and critical paths

Propose Candidate entries for code generation, project-file generation, entitlements, signing,
privacy manifests, release/archive configuration, migrations, and deployment
scripts. Assign human reviewers for signing and release paths.

<!-- platform-stage: stop-and-recover -->
## 6. Stop and recover

Stop on unknown scheme/destination, missing Xcode/CocoaPods, unresolved signing,
dirty generated files, or CI-only secrets. Ask the owner for evidence, update
the calibration Candidate, and rerun the same check; never downgrade it.

<!-- platform-stage: verify-platform-adoption -->
## 7. Verify iOS adoption

Success requires all ten calibration stages, repository-evidenced commands,
separate local/hosted results, a reviewed PR, and lifecycle closure. A minimal
SPM fixture in AI Cockpit is not evidence for this adopter's Xcode app.
