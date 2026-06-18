---
author: Ray
title: "Installation"
description: Installation and quick start guide for AI Cockpit.
keywords:
  - ai-cockpit
  - installation
  - quick-start
  - ai-agents
---

# Installation

Install AI Cockpit into an existing repository:

```sh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh)" -- --stack rust --update-makefile
```

Start a governed AI task:

```sh
make ai-start TASK=example_change TITLE="Example change" MODE=code
```

Edit the generated Contract:

```text
.ai/work-items/active/example_change.contract.json
```

Before changing project files, replace the skeleton placeholders and confirm this minimum checklist:

- `scope` contains every file or path pattern the task may change, and `outOfScope` states explicit boundaries.
- `sources`, `acceptance`, and `verification` describe the evidence, done conditions, and registered checks.
- `unknowns` is empty, `notCodable` is `false`, and `executionDecision.status` is `continue`.
- `agentCapability.canImplement` and `agentCapability.canVerify` are `true`; human decisions remain explicit.
- Run `make ai-checkpoint STAGE=before_edit` before implementation.

Update the Summary before finishing:

```text
.ai/work-items/active/example_change.summary.json
```

Run the finish flow:

```sh
make ai-finish TASK=example_change
```

`ai-finish` runs the registered checks, updates the Summary with execution evidence, regenerates status, and archives the Contract/Summary pair. A successful walkthrough ends with no files under `.ai/work-items/active/`, an archive pair under `.ai/work-items/archive/<year>/`, and `make check-ai-status-consistency` passing.

## Local Install

From a local clone:

```sh
/path/to/ai-cockpit-template/install.sh --stack rust --update-makefile
```

## Safer Two-Step Install

```sh
curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh -o install-ai-cockpit.sh
sh install-ai-cockpit.sh --stack rust --update-makefile
```

## Versioned Install

Use a tag or commit SHA for reproducible installs. The generic GitHub archive endpoint also accepts branch names:

```sh
AI_COCKPIT_TEMPLATE_REF=v0.2.0 \
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh)" -- --stack rust --update-makefile
```

## Options

```text
--dry-run          Show actions without writing files.
--force            Overwrite existing AI Cockpit files.
--upgrade          Back up and replace managed runtime, policy, and agent marker files.
--upgrade-with-active
                   Permit a high-risk upgrade while active Work Item JSON exists.
--with-examples    Copy examples/ into the target repository.
--update-makefile  Append "include Makefile.ai" to the target Makefile.
```

By default, the installer is conservative:

- It writes `Makefile.ai` and `Makefile.ai.stack` instead of modifying an existing Makefile.
- It appends AI Cockpit sections to existing `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md`.
- It installs Cursor rules under `.cursor/rules/ai-cockpit.mdc`.
- It skips existing files unless `--force` is provided.
- It creates clean active/archive directories and does not copy the template repository's Work Item history.

The installed runtime includes `scripts/ai_check_pr.py`, the `check-ai-pr` Make target, and Contract-aware guard wiring. The distribution template is exercised independently from the repository-root Makefile in CI.

Stack selection configures quality-command starting points. It does not infer the target repository's production and test directories. Review `.ai/guards/coverage_policy.yaml` during adoption and add the project's layouts before relying on Coverage Guard as a required gate.

## Common Failures and Recovery

- `No rule to make target 'ai-start'`: rerun the installer with `--update-makefile`, or add an active `include Makefile.ai` line to the project Makefile. A commented line is not active.
- Contract validation reports placeholders or unknowns: complete the checklist above; do not start implementation by weakening required checks.
- Status consistency fails: run `make repair-ai-status` only when there is no active item or exactly one paired Contract/Summary. Repair unpaired or multiple active records manually.
- A project quality command is missing: install/configure the selected stack tools or edit `Makefile.ai.stack`; the generic preset intentionally fails closed.
- An active task must be abandoned: preserve or document relevant evidence, then remove/archive the pair deliberately. Do not delete a single record from the pair.

## Upgrade

The installed `.ai/cockpit/version.json` records the distribution and Contract schema version. Use `--upgrade` for an existing installation:

```sh
AI_COCKPIT_TEMPLATE_REF=v0.3.0 \
  sh install-ai-cockpit.sh --upgrade --stack rust
```

By default, upgrade stops before writing if `.ai/work-items/active/` contains Work Item JSON. Finish and archive the active task first. `--upgrade-with-active` is an explicit high-risk override for recovery scenarios where changing governance semantics during a task is intentional.

Before replacement, managed files are copied under `.ai/cockpit/upgrade-backups/<timestamp>/`. This directory and active review records are added to the managed `.gitignore` rules. Agent sections between the AI Cockpit markers are replaced as one managed block. If an existing `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` has no markers, upgrade preserves its content and appends the managed section. Customized guards and `checks.yaml` are backed up before the source version is installed. The installer validates version metadata before writing, rejects distribution or Contract-schema downgrades, validates the installed managed runtime afterward, and automatically restores backed-up files if installation or post-copy validation fails. Review and remove successful-upgrade backups when they are no longer needed. `--force` replaces files without an upgrade backup and is intended for disposable or externally backed-up installations.

If you did not use `--update-makefile`, add this line to your project Makefile:

```make
include Makefile.ai
```

After successful Work Item finish/archive, configure pull-request CI to fetch full Git history and run:

```sh
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD origin/main)"
```

For GitHub Actions, a complete minimal job is:

```yaml
jobs:
  ai-governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD origin/${{ github.base_ref }})"
      - run: make quality
```

The PR check requires at least one archive Contract/Summary pair in the PR diff and validates every changed pair against the complete merge-base diff.

## Runtime Requirements

- Python 3.10 or newer.
- Git with merge-base and three-dot diff support.
- POSIX shell and GNU Make-compatible command behavior.
- Linux and macOS are the supported CI/runtime environments. Native Windows shells are not currently supported; use WSL or another POSIX environment.
