---
author: Ray
title: "Install AI Cockpit"
description: "Interactive-first installation, review, rollback, and calibration boundary."
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Install AI Cockpit

<!-- public-quality-target: ai-cockpit-quality -->

The default human path is the interactive installer. Run it from the target Git
repository:

<!-- command-evidence: adopter_required -->
```bash
./install.sh --interactive
```

A no-argument TTY invocation opens the same wizard. Explicit installer flags
remain the stable automation interface; a no-argument non-TTY invocation fails
closed instead of waiting for input.

## What the wizard shows

The wizard presents one reviewable sequence:

1. Target Repository
2. Readiness
3. Installation Mode
4. Governance Profile
5. Planned Changes
6. Conflict Review
7. Explicit Confirmation
8. Installation
9. Verification
10. Next Action

Before confirmation it shows the repository path, Git and tool readiness,
New Adoption / Upgrade / Dry Run mode, a Lite / Standard / Strict profile
choice, planned add and modify counts, source-code impact, the installation
branch, and every detected conflict. Standard is the display default.

The profile choice records installation intent only. The installer does not
activate Lite, Standard, or Strict policy. Project calibration remains a
separate Work Item after installation.

## Safety boundary

Until an explicit `yes`, the target is read-only. Dry Run, blocked readiness,
unresolved conflicts, blank or declined confirmation, EOF, and interruption do
not invoke the write transaction.
If readiness or conflict evidence is `Unknown`, stop and resolve it before
installation.

The installer does not commit, push, create a pull request, merge, delete the
successful installation branch, activate Strict, or report installation as
completed calibration. On transaction failure, the existing Installer restores
the original branch or detached HEAD and rolls back created or replaced files,
managed sections, Makefile content, and agent markers. Inspect the reported
target state before retrying; do not infer recovery from a generic failure
message.

## Automation and prompt-assisted use

For deterministic automation, pass explicit options such as `--dry-run`,
`--upgrade`, `--create-adoption`, `--stack`, and `--update-makefile`. Prompt-led
agent installation is an auxiliary path: require the agent to run the same
read-only plan, show conflicts and planned files, and wait for explicit
confirmation before invoking the installer.

## After installation

After installation, start a separate project-calibration Work Item.
Review the generated Work Item and installation branch. The installer leaves
Git publication to the normal human-reviewed lifecycle. Start calibration only
as a separate Work Item; installation alone is not production-readiness
evidence.

## More detail

- [Strict installation and supply-chain verification](installation-security.md)
- [Project calibration guide](calibration.md)
- [Calibration-session model for maintainers and auditors](../reference/calibration-session-model.md)
- [Installation troubleshooting](../troubleshooting/installation.md)
- [Interactive wizard architecture](../architecture/interactive-installation-wizard.md)
- [iOS](examples/ios.md), [Android](examples/android.md), and [Java](examples/java.md) examples
