---
author: Ray
title: "Troubleshooting"
description: Recovery guide for common AI Cockpit installation and adoption failures.
keywords:
  - ai-cockpit
  - troubleshooting
  - recovery
  - installation
  - adoption
---

# Troubleshooting

Use this page when installation or adoption fails and you need a direct recovery path.

## Wizard recovery

- If the Installation Wizard detects a dirty worktree, missing remote/default branch, or a managed conflict, stop and resolve that repository condition before confirming. Dry Run is safe for inspecting the plan.
- If the Calibration Wizard shows `Unknown` or `stale`, do not confirm around it. Record the missing fact, revalidate the affected stage, and rerun the self-check or simulation.
- If input ends with EOF or Ctrl+C, resume with `make cockpit-calibration-wizard`; the persisted Session is not treated as activated. A failed activation preserves the previous Active configuration.
- If a mobile command is unavailable, verify the repository's own Gradle Wrapper/Xcode/CocoaPods setup and JDK requirement. The template does not install or switch external toolchains.

## Common Failures

- `./gradlew` fails before any AI Cockpit check runs: first identify the project type. For a Java project, use the JDK required by its Gradle Wrapper; Java compatibility CI uses 21. For Android, use the JDK required by the Wrapper/AGP combination; the Android smoke uses 17. Then verify `./gradlew` itself before debugging Cockpit commands. AI Cockpit does not install or switch JDK versions.
- `No rule to make target 'ai-start'`: rerun the installer with `--update-makefile`, or add an active `include Makefile.ai` line to the project Makefile. A commented line is not active.
- Contract validation reports placeholders or unknowns: complete the checklist in [Installation](../getting-started/installation.md); do not weaken required checks to make the task start.
- Status consistency fails: run `make repair-ai-status` only when there is no active item or exactly one paired Contract/Summary. Repair unpaired or multiple active records manually.
- A project quality command is missing: install or configure the selected stack tools, or edit `Makefile.ai.stack`; the generic preset is intentionally fail-closed.
- Android/Java preset commands do not exist in this repo: treat `testDebugUnitTest`, `spotlessCheck`, and `lint` as starting points only, then replace them with the actual variant-aware Gradle tasks that `./gradlew tasks` shows for your flavor layout.
- Android coverage is too broad at first pass: keep `.ai/guards/coverage_policy.yaml` report-only while you map `app/src/main/**`, `*/src/main/**`, `app/src/test/**`, and `app/src/androidTest/**` for the modules that own each variant.
- An active task must be abandoned: preserve or document relevant evidence, then remove or archive the pair deliberately. Do not delete a single record from the pair.

## Recovery Path

1. Confirm the repository still has a clean, committed baseline.
2. Check whether the issue is a missing project command, a stack mismatch, or a Work Item lifecycle problem.
3. Use [Installation](../getting-started/installation.md) for the guided adoption flow and [Upgrade](upgrade.md) if the issue came from replacing managed files.
4. Re-run the relevant `make` target after correcting the root cause.

The troubleshooting page is intentionally short. It exists to point you back to the right workflow or reference page without duplicating the full installation guide.
