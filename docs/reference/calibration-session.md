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
make cockpit-calibrate-session ARGS="record-evidence --stage repository_role --observed-evidence README.md --candidate-change 'no change: repository role confirmed' --owner repository-owner --reviewer repository-reviewer --decision PASS --decision-reason 'repository evidence is complete'"
make cockpit-calibrate-session ARGS="pause"
make cockpit-calibrate-session ARGS="resume"
make cockpit-calibrate-session ARGS="review"
make cockpit-calibrate-session ARGS="stage-self-check"
make cockpit-calibrate-session ARGS="full-self-check"
make cockpit-calibrate-session ARGS="simulate"
make cockpit-calibrate-session ARGS="prepare-candidate"
make cockpit-calibrate-session ARGS="confirm --phase reviewer --candidate-revision <revision> --candidate-digest <sha256>"
make cockpit-calibrate-session ARGS="confirm --phase owner --candidate-revision <revision> --candidate-digest <sha256>"
make cockpit-calibrate-session ARGS="activate"
```

The schema version 2 JSON Session stores answers, transition events,
stage/full self-checks, Governance Simulation, both human confirmation records,
and one complete structured checklist evidence record per stage. That record
contains observed evidence, Candidate change, intended Owner and Reviewer,
PASS/STOP, decision reason, and retry step. `answer` and `record-evidence` are
separate transitions; neither manual JSON editing nor Work Item prose can
substitute for the persisted fields.

`Unknown`, `STOP`, missing checklist fields, and stale evidence machine-block
review, full self-check, Governance Simulation, Candidate preparation,
confirmation, and activation in the core state machine used by both the direct
CLI and Wizard. Changing an answer or checklist record marks the Candidate
stale and invalidates current confirmations. `back` and `review` do not erase
evidence.

Candidate preparation occurs before confirmation. It snapshots all ten
answers and checklist records, assigns a monotonically increasing revision,
and computes a SHA-256 digest over canonical JSON. Reviewer and Owner phase
records must each supply and persist that exact revision and digest. The phase
names bind decisions to Candidate content; they do not authenticate people or
prove role separation. Keep trusted actor identity evidence in the governed
Work Item or an external identity system.

Activation recomputes Candidate identity and commits Active plus activated
Session through one two-file rollback transaction. If staging or either
replacement fails, every attempted path is restored to its transaction-start
bytes or absence. A rollback failure reports `consistency is unproved` and
never reports activation success. This is an exact recovery guarantee, not a
claim that two filesystem replacements are physically atomic.

Schema version 1 Sessions remain readable through fail-closed migration.
Missing checklist evidence remains incomplete, digest-free confirmations
become non-authorizing legacy history, and a legacy activated state becomes
paused with `legacy_unverified` Active status until it is re-evidenced,
prepared, and confirmed under version 2.

This scaffold proves repository governance state and evidence only; it is not
an enterprise security, identity, sandbox, immutable-audit, or compliance
control.

## Recovery and blocking rules

`Unknown` is always visible and blocking; it cannot be silently converted into
approval. `Not Applicable` requires a reason. If an upstream answer changes,
downstream evidence becomes stale and must be revalidated before a new
Candidate is prepared. A changed Candidate requires both confirmation phases
again. `Pause`, EOF, Ctrl+C, and a safe quit preserve the last persisted state
without claiming completion. A transaction failure reports the failed step,
rollback result, and whether consistency was proved.
