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

<!-- doc-domain: wizard-start -->
## Start the Wizard

From a clean target repository with at least one commit, resolve the published
tag, download that tag's installer, and start the Installation Wizard. The
copy-ready defaults point to the canonical public repository; override them only
for an explicitly verified source. For a private or mirrored source, use
[Installation](installation.md#choose-an-entrypoint) instead of guessing a URL.

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
