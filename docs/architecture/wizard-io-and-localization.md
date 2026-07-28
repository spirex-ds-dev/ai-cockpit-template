---
author: Ray
title: "Wizard IO and Localization"
description: TTY-safe input controls and exact-parity Wizard message resources.
keywords:
  - interactive-wizard
  - localization
  - accessibility
---

# Wizard IO and Localization

`ai_wizard_io` is the shared, fail-closed input boundary for later Wizard
steps. Non-TTY execution never waits for input; blank, EOF, and Ctrl+C do not
confirm dangerous actions. Back, Pause, Quit, and Help are represented as
explicit `Action` values, and status output remains readable without color.

`ai_wizard_localization` normalizes the Wizard's `ja`, `en`, and `zh-CN`
language aliases independently from project documentation language. Resources
are checked for exact keys and `{placeholder}` parity before user-visible use;
unsupported languages raise an error instead of silently falling back.

Both executable adapters consume this same resource layer:
`ai_install_wizard.py` localizes installation selection, plan labels,
confirmation, STOP, and result chrome, while `ai_calibration_wizard.py`
localizes stage presentation, navigation, pause/recovery, Unknown, and N/A
chrome. Each CLI accepts `--language`; resolution order is the explicit option,
`AI_COCKPIT_LANGUAGE`, the supported system locale, and then the safe Japanese
default. The `C` and `POSIX` locales mean “no language preference” and therefore
use that default. An unsupported explicit, environment, or named system locale
fails closed.

Localization applies only to presentation chrome. Repository paths, commands,
stage IDs, status values, detected facts, user answers, and machine evidence are
inserted unchanged. Executable Japanese tests cover both adapters; resource
parity or an unused import alone is not accepted as Japanese capability
evidence. This boundary does not claim general model fluency or human
translation review.
