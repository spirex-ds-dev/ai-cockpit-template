---
author: Ray
title: "iOS Installation Example"
description: Beginner-safe AI Cockpit calibration example for iOS repositories.
keywords: [ai-cockpit, ios, xcode, swift, installation]
---

# iOS Installation Example

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
| Steps 1–4 | Nothing; finish discovery first | Installation Step 5 |
| Steps 5–6 | Copy table rows 1–4, one at a time | Installation Step 7 |
| Steps 7–8 | Nothing; complete write and Adoption closure | Installation Step 9 |
| Step 9 | Use table row 5 inside Calibration | Return to and complete the rest of Installation Step 9, then Step 10 |
| A STOP produced by platform rows 1–5 | Copy table row 6 | The same blocked platform stage |
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
signing, simulator, CocoaPods, or hosted-CI facts. Do not begin Stage 1 now;
wait for me to paste the first Primary action table row. After every later
stage, wait for my answer and make no changes.
```

Example: finding `MyApp.xcworkspace` means “an Xcode workspace exists”; it does
not mean Xcode or a working scheme exists. Recommendation: start from the
`swift` preset, then calibrate project-specific commands; stop for the iOS
owner if scheme/destination evidence is missing.

### Primary action table

Copy one row at a time:

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| Stage | Exact request | Example result and choice | PASS | STOP/contact |
| --- | --- | --- | --- | --- |
| 1 Detect | “List `.xcodeproj`, `.xcworkspace`, `Package.swift`, dependency files, app/extensions, schemes, tests, and CI. Change nothing.” | `MyApp.xcworkspace` exists; classify as workspace, not proof of a runnable app. | Layout and owners are clear. | Mixed/unknown layout; iOS owner. |
| 2 Toolchain | “Show project/CI evidence for Xcode/Swift versions, dependency manager, scheme, destination, signing, simulator/device, and hosted macOS.” | CI pins Xcode 16; local availability remains separately Unknown. | Every required tool/environment has evidence. | Missing version, scheme, destination, signing, or host; iOS/release owner. |
| 3 Boundaries | “Propose `swift` or `generic`, maintained source, generated/vendor/output exclusions, and evidence for each.” | `swift` is a starting preset; non-SPM commands still need calibration. | Each inclusion/exclusion is explained. | Preset would hide mixed layout; module owner. |
| 4 Commands | “Copy exact repository/CI commands and explain scheme, destination, configuration, prerequisite, success, and failure. Do not invent.” | An evidenced test command is separate from archive/signing. | Commands and environments are evidenced. | Missing command or secret/device; iOS/CI owner. |
| 5 Calibrate | “Propose Candidate entries for generators, entitlements, privacy manifest, signing, archive/release, migrations, deployment, and reviewers. Do not write or activate.” | Signing paths require a release reviewer. | Proposed diff shows all critical/generated paths. | Owner or regeneration rule missing; build/release owner. |
| 6 Recover | “Preserve the failure evidence, name the missing fact and owner, update the Candidate only after evidence arrives, and rerun the same check.” | Unknown destination stays blocking. | Same requirement later passes. | Reject the weaker substitute, STOP, and contact the owner named in the blocked stage; rerun that stage after evidence arrives. |
| 7 Verify | “Show an evidence table with one row per calibration/lifecycle requirement and columns for evidence path or URL, commit SHA, PASS/STOP, and missing item; include local/hosted results, PR Head SHA, human merge, closure, and branch deletion.” | A minimal SPM fixture is not adopter Xcode evidence. | All rows belong to this repository and commit and none is missing. | Any missing lifecycle/platform evidence; repository owner. |

<!-- platform-filled-example: seven-stages -->
### Filled-answer example: fictional `SampleNotes`

Each row is independent. A STOP row does not continue. Obtain the owner's
answer, rerun the same stage, and continue only after PASS. Later rows show the
display after an earlier STOP has been resolved.

| Stage | Example agent answer | User answer to copy | Success display | Information to provide when stopped |
| --- | --- | --- | --- | --- |
| 1 | “Found `SampleNotes.xcworkspace`, an app target, and a unit-test target; shared scheme is unconfirmed.” | `The shared scheme is Unknown. Make no changes and ask the iOS owner.` | Workspace and target inventory. | Give every detected path to the iOS owner. |
| 2 | “CI declares Xcode 16.2, scheme SampleNotes, and iPhone 16 Simulator.” | `Record those three as candidates and STOP. Ask the iOS owner for local-availability evidence, then rerun Stage 2.` | Source lines from project/CI. | Give the version and CI filename to the owner. |
| 3 | “`Sources/` is maintained; `DerivedData/` is output. Propose the swift preset as a starting point.” | `I accept the evidenced boundaries. Do not finalize non-SPM commands.` | Separate included and excluded paths. | Give undecidable paths to the module owner. |
| 4 | “Copied the exact test command from CI; archive/signing command remains unconfirmed.” | `Record only the test command and STOP with archive/signing as Unknown.` | Command source, prerequisites, and success display. | Give the command and missing facts to CI/release owners. |
| 5 | “Entitlements and privacy manifest are critical; Release Team reviews signing.” | `Propose only the Candidate diff. Do not write or activate it.` | Proposed paths and reviewer. | Give ownerless items to the release owner. |
| 6 | “Test failed because the simulator is absent.” | `Preserve the log, provide the same destination, and rerun the same test.` | The same command succeeds. | Give the log, Xcode version, and destination to the owner. |
| 7 | “Checked PR #123, Head SHA, hosted check, merge, closure, and branch deletion.” | `Show links for every item and mark iOS adoption PASS only if none is missing.` | All seven evidence kinds bind to the same commit. | Give missing items and the PR URL to the repository owner. |

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
