---
author: Ray
title: "Interactive Installation Wizard"
description: "The eight-step, read-only-until-confirmed installation flow."
---

# Interactive Installation Wizard

`scripts/ai_install_wizard.py` orchestrates a fixed eight-step review flow over the
read-only facts produced by `ai_installer_detection.py`:

1. Target Repository
2. Repository Readiness
3. Installation Mode
4. Project Stack
5. Installation Options
6. Adoption Branch
7. Installation Plan Review
8. Installation/Result

Each step includes purpose, rationale, detected facts, the suggested value, option
impact, an example, write status, expected result, stop condition, and checklist.
The complete plan is rendered before confirmation. A declined confirmation and
Dry Run do not mutate the target repository. The wizard explicitly does not
commit, push, open a PR, or merge.

The executable accepts `--language ja|en|zh-CN` and otherwise uses the shared
Wizard locale resolution policy. Selection labels, plan-field labels,
confirmation, STOP, cancellation, and result chrome come from exact-parity
resources. Detected facts, paths, commands, option values, and evidence remain
unchanged rather than being machine-translated. Unsupported language requests
fail before installation begins.

After affirmative confirmation, the wizard constructs the existing
`install_ai_cockpit.Installer` and delegates the transaction to it. It does not
duplicate transaction, conflict, rollback, or Work Item creation behavior.
Scripted execution injects `input_fn`, `output`, and the installer factory so the
write boundary can be tested without a TTY.
