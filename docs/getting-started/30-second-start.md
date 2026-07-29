---
author: Ray
title: "30-Second Start"
description: "The smallest documented path from a clean checkout to a reviewable AI Cockpit Work Item."
keywords:
  - installation
  - quick-start
  - work-item
---

# 30-Second Start

For prerequisites, every Wizard choice, scaffold inspection, all ten
calibration stages, the first PR, recovery, and platform examples, continue
with the complete [Installation](installation.md).

<!-- doc-domain: wizard-start -->
## Start the Wizard

The recommended beginner path is to paste this into the coding agent that has
your target project open:

```text
Help me begin AI Cockpit installation from the canonical public repository
https://github.com/spirex-ds-dev/ai-cockpit-template.git. Work read-only first.
Verify that this is the intended Git project, it has an initial commit, its
worktree is clean, and Python 3.11+, Git, GNU Make, and curl are available.
Read the public release.json, resolve a fixed published tag, and explain the
release/tag/digest evidence in plain language. Do not download or execute
anything until you show the exact plan and I approve only that installation
step. Do not commit, push, create or merge a PR, delete, or publish.
```

Expected result: a plain-language prerequisite and fixed-release report plus
one bounded approval question. For a private or mirrored source, stay in the
complete [Installation](installation.md) route and ask the source owner for its
trust evidence.

### Advanced manual fallback

The block below is for an experienced operator who cannot use an agent. Paste
it only in the target repository's terminal. Success means the Wizard opens;
on any error, stop and use the complete Installation recovery table.

<!-- command-evidence: adopter_required -->
```sh
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "$RAW_BASE/main/release.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["releaseTag"])')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "$RAW_BASE/$RELEASE_TAG/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" sh "$INSTALLER" --interactive
```

<!-- doc-domain: does -->
## What it does

The Wizard detects repository facts, lets you choose New Adoption, Upgrade, or
Dry Run, and shows a reviewable write plan. It writes only after explicit human
confirmation.

<!-- doc-domain: does-not -->
## What it does not do

It does not calibrate project quality commands, prove production readiness,
commit, push, create or merge a PR, delete branches, publish a release, or grant
enterprise assurance.

<!-- doc-domain: after-installation -->
## What remains after installation

Finish the generated Adoption Work Item, obtain the required human approvals,
configure the Project Profile/Guards/CI in a separate Work Item, run calibration,
and verify adoption readiness. Continue with the
[Standard Adoption Guide](standard-adoption-guide.md) and
[Security and Release Verification](security-release-verification.md).
