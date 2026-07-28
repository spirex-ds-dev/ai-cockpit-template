---
author: Ray
title: "RFE-151 Calibration Transaction Design"
description: Fail-closed Calibration readiness, Candidate-bound confirmation, complete checklist evidence, and recoverable Active/Session persistence.
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# RFE-151 Calibration Transaction Design

## Problem

The current `CalibrationSession` has four authority gaps:

1. `answerType=unknown` still sets a stage to `complete`; the Wizard adds a
   partial guard, but the direct CLI and core review/check methods remain
   weaker.
2. Reviewer and Owner confirmations are recorded before a Candidate exists and
   do not identify the configuration that was reviewed.
3. The ten-stage beginner checklist contains observed evidence, Candidate
   change, Owner/Reviewer, and PASS/STOP columns that have no complete
   structured Session location.
4. Activation atomically replaces only Active. The caller saves Session
   afterward, so a Session failure can leave Active and Session contradictory.

These are release-blocking governance defects. They can turn incomplete,
stale, or partially persisted calibration state into an apparent approval.

## Selected design

### Core owns every readiness predicate

`CalibrationSession` becomes the single authority used by both direct CLI and
Wizard. A stage is ready only when:

- its answer type/value/reason are valid;
- the answer type is not `unknown`;
- its structured checklist record is complete;
- its decision is `PASS`;
- it is not stale.

Review, full self-check, Governance Simulation, Candidate preparation,
confirmation, and activation all call the same blocker computation. The Wizard
may render blockers but cannot weaken or supplement the core decision.

### Schema version 2 checklist evidence

Each stage persists one `checklistEvidence` object:

- `observedEvidence`: non-empty list of repository-relative paths, URLs, or
  plain evidence identifiers;
- `candidateChange`: non-empty description or explicit evidence-backed
  `no change` reason;
- `owner`: intended responsible role or identity reference;
- `reviewer`: intended reviewer role or identity reference;
- `decision`: `PASS` or `STOP`;
- `decisionReason`: non-empty reason;
- `retryStep`: required for `STOP`, optional for `PASS`;
- `recordedAt`: offset-aware timestamp.

The existing `checklist` object continues to own answer type/value/reason.
Together they cover every column in the authoritative ten-row installation
checklist. Phase confirmations still do not prove actor identity.

Schema version 1 is migrated in memory to version 2. Missing structured
evidence is created as incomplete, an Unknown answer is changed from
false-complete to blocked, and old digest-free confirmations are retained only
as non-authorizing legacy history. Migration never manufactures PASS evidence
or readiness.

### Candidate preparation precedes confirmation

Candidate preparation is an explicit transition after review, full self-check,
and Governance Simulation pass. It canonicalizes:

- Session ID and language;
- all ten answer records;
- all ten structured evidence records.

Canonical UTF-8 JSON with sorted keys and compact separators is hashed with
SHA-256. The persisted Candidate contains `status=prepared`, a monotonically
increasing `revision`, `digestAlgorithm=sha256`, `digest`, and the immutable
configuration snapshot.

Both `reviewer` and `owner` confirmation commands require the exact visible
revision and digest. Confirmation records persist those values. Any answer or
structured evidence mutation marks the Candidate stale and clears current
authorizing confirmations. Historical transition events remain.

Activation recomputes the canonical digest and requires:

- no blocker;
- current full self-check and Governance Simulation passes;
- a prepared Candidate whose digest still matches its configuration;
- both confirmation phases bound to that exact revision and digest.

### Recoverable two-file persistence

Activation is committed by one helper that owns both `active_path` and
`session_path`.

1. Capture whether each path exists and its exact bytes.
2. Build the final Active bytes and activated Session bytes in memory.
3. Write and fsync temporary files in each destination directory.
4. Replace Active.
5. Replace Session.
6. On any exception, restore both paths to their captured existence and bytes.
7. If rollback itself fails, raise a compound error that explicitly says
   consistency is unproved; never report activation success.

This is a rollback transaction, not a claim that two filesystem replacements
are physically atomic. A newly created path is removed during rollback; a
pre-existing path is restored byte-for-byte.

Ordinary Session saves also use temporary-file replacement so a partial write
cannot corrupt the prior Session.

## Interface changes

The direct CLI adds:

- `record-evidence` with stage and structured checklist fields;
- `prepare-candidate`;
- required `--candidate-revision` and `--candidate-digest` for `confirm`.

The Wizard exposes equivalent methods and renders Session ID, path, Candidate
revision/digest/status, blocking stages/fields, and transaction result. Its
activation path calls the same two-file transaction helper as the CLI.

## Alternatives rejected

### Keep Unknown blocking only in the Wizard

Rejected because direct CLI remains an authority bypass.

### Generate and hash the Candidate during activation

Rejected because a human cannot confirm an identity that does not yet exist.

### Store checklist evidence only in Work Item prose

Rejected because the Session cannot deterministically prove completeness or
bind the evidence to the Candidate digest.

### Write Session before Active without rollback

Rejected because it reverses, but does not remove, the split-brain failure
window.

### Introduce a database or lock service

Rejected as outside the repository-governance and standard-library boundary.
The local two-file rollback transaction is sufficient for the required
failure model.

## Compatibility and non-claims

- Existing schema version 1 Sessions remain readable but blocked until missing
  evidence is supplied and a new Candidate is prepared and confirmed.
- Confirmation phase names remain `reviewer` and `owner`.
- The Session records evidence and decisions; it does not authenticate people,
  provide non-repudiation, create an immutable audit service, or guarantee
  enterprise compliance.
- This Work Item does not alter Project Profile meaning, nested Make execution,
  or release metadata.

## Verification

Red-first regressions cover all-Unknown input, incomplete structured evidence,
wrong digest/revision, Candidate mutation after confirmation, v1 migration,
Active failure, Session failure after Active replace, rollback error reporting,
and successful direct CLI/Wizard transactions. Full repository quality,
distribution checks, PR aggregate ownership, Hosted CI, merge, closure, and
branch cleanup remain mandatory.
