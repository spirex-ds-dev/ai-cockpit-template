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
sh -c "$(curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh)" -- --stack rust
```

Start a governed AI task:

```sh
make ai-start TASK=example_change TITLE="Example change" MODE=code
```

Edit the generated Contract:

```text
.ai/work-items/active/example_change.contract.json
```

Update the Summary before finishing:

```text
.ai/work-items/active/example_change.summary.json
```

Run the finish flow:

```sh
make ai-finish TASK=example_change
```

## Local Install

From a local clone:

```sh
/path/to/ai-cockpit-template/install.sh --stack rust
```

## Safer Two-Step Install

```sh
curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh -o install-ai-cockpit.sh
sh install-ai-cockpit.sh --stack rust
```

## Versioned Install

Use a tag or commit SHA for reproducible installs. The generic GitHub archive endpoint also accepts branch names:

```sh
AI_COCKPIT_TEMPLATE_REF=v0.2.0 \
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/xinglun/ai-cockpit-template/main/install.sh)" -- --stack rust
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

## Upgrade

The installed `.ai/cockpit/version.json` records the distribution and Contract schema version. Use `--upgrade` for an existing installation:

```sh
AI_COCKPIT_TEMPLATE_REF=v0.3.0 \
  sh install-ai-cockpit.sh --upgrade --stack rust
```

By default, upgrade stops before writing if `.ai/work-items/active/` contains Work Item JSON. Finish and archive the active task first. `--upgrade-with-active` is an explicit high-risk override for recovery scenarios where changing governance semantics during a task is intentional.

Before replacement, managed files are copied under `.ai/cockpit/upgrade-backups/<timestamp>/`. This directory and active review records are added to the managed `.gitignore` rules. Agent sections between the AI Cockpit markers are replaced as one managed block. Customized guards and `checks.yaml` are backed up before the source version is installed. The installer validates version metadata before writing, rejects distribution or Contract-schema downgrades, validates the installed managed runtime afterward, and automatically restores backed-up files if installation or post-copy validation fails. Review and remove successful-upgrade backups when they are no longer needed. `--force` replaces files without an upgrade backup and is intended for disposable or externally backed-up installations.

If you did not use `--update-makefile`, add this line to your project Makefile:

```make
include Makefile.ai
```

After successful Work Item finish/archive, configure pull-request CI to fetch full Git history and run:

```sh
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD origin/main)"
```

The PR check requires at least one archive Contract/Summary pair in the PR diff and validates every changed pair against the complete merge-base diff.

## Runtime Requirements

- Python 3.10 or newer.
- Git with merge-base and three-dot diff support.
- POSIX shell and GNU Make-compatible command behavior.
- Linux and macOS are the supported CI/runtime environments. Native Windows shells are not currently supported; use WSL or another POSIX environment.
