---
author: Ray
title: Calibration Session
description: The adopter-executable ten-stage first-calibration lifecycle.
---

# Calibration Session

`scripts/ai_calibrate.py session` provides the first-calibration scaffold. It is a persisted, reviewable Session; Runtime installation alone is not calibration completion.

The interactive adapter is available as `make cockpit-calibration-wizard` (or `python3 scripts/ai_calibration_wizard.py --root .`). It owns presentation, input validation, navigation, and recovery display only; `CalibrationSession` remains authoritative for state transitions, stale evidence, checks, confirmations, and activation. Use `--summary` to inspect the current persisted state without advancing it.

## Lifecycle

The Session contains exactly ten ordered stages: repository role, language and stack, source boundaries, test boundaries, generated artifacts, critical paths, quality commands, review requirements, risk and unknowns, and adoption readiness. Japanese (`ja`) is the default language. Each checklist accepts `Y/N`, an alternative/input value, `Unknown`, or `Not Applicable`; `Not Applicable` requires a reason.

```sh
make cockpit-calibrate-session ARGS="start --session-id first-calibration"
make cockpit-calibrate-session ARGS="answer --stage repository_role --answer Y --answer-type yes_no"
make cockpit-calibrate-session ARGS="pause"
make cockpit-calibrate-session ARGS="resume"
make cockpit-calibrate-session ARGS="review"
make cockpit-calibrate-session ARGS="stage-self-check"
make cockpit-calibrate-session ARGS="full-self-check"
make cockpit-calibrate-session ARGS="simulate"
make cockpit-calibrate-session ARGS="confirm --phase reviewer"
make cockpit-calibrate-session ARGS="confirm --phase owner"
make cockpit-calibrate-session ARGS="activate"
```

The JSON Session stores answers, transition events, stage/full self-checks, Governance Simulation, and both human confirmation records. Changing an upstream answer marks completed downstream stages stale; stale evidence is retained but cannot activate a Candidate until revalidated. `back` and `review` do not erase evidence.

Candidate activation writes through a temporary file and atomic replacement only after all ten stages, checks, and both confirmations pass. A failed activation is fail closed and leaves the existing Active configuration unchanged. This scaffold proves repository governance state and evidence only; it is not an enterprise security, identity, sandbox, immutable-audit, or compliance control.

## Recovery and blocking rules

`Unknown` is visible and blocking when it affects readiness; it cannot be silently converted into approval. `Not Applicable` requires a reason. If an upstream answer changes, downstream evidence becomes stale and must be revalidated before review or activation. `Pause`, EOF, Ctrl+C, and a safe quit preserve the last persisted state without claiming completion. A partial failure reports completed and incomplete actions separately and leaves the prior Active configuration in place.
