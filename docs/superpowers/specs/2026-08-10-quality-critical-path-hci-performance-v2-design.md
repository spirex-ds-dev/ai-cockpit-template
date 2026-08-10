---
author: Ray
title: "Quality Critical Path HCI Performance V2 Design"
description: "Source-bound quality measurement, safe project-test sharding, and continuous feedback design."
keywords:
  - quality
  - performance
  - hosted-measurement
  - hci
---

# Quality Critical Path HCI Performance V2 Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Goal

Shorten trustworthy developer feedback without reducing the test manifest,
coverage floor, release/security gates, or failure evidence. A green outcome is
allowed only after five comparable Hosted candidate samples meet every stated
threshold.

## Measurement contract

`quality_measurements.py` will validate a set of source-bound samples. A valid
sample has one commit SHA, tree digest, runner image/OS/Python tuple, workflow
identity, and attempt; baseline and candidate sets are never merged. Percentiles
use nearest-rank. Missing, failed, cancelled, stale, or mismatched samples make
the comparison fail closed.

`run_quality_gate.py` will emit per-gate identity, timing, progress and outcome
facts. `summarize_quality_gates.py` will expose collection/result/coverage/slow
test and cache facts without treating a cache hit as verification.

## Test manifest and sharding

`quality_test_manifest.py` will define one complete project-test manifest:
pytest node IDs plus shell/E2E commands. It assigns every entry to exactly one
named shard using stored historical durations, never file count. The serial
`project-test` entrypoint consumes the same manifest. Hosted jobs run shards on
isolated runners and create per-shard JUnit, coverage, timing and receipt files.
The aggregate verifies exact ownership and source identity before coverage merge.

## HCI and failure behavior

The coordinator reports an initial stage and a 30-second heartbeat containing
current gate, elapsed time, completed/total gates, last progress and evidence
path. A failure emits a red block immediately with gate, test when known,
recovery and outcome path. Success emits the green block with wall time and
coverage. A missing shard artifact is a red outcome, not an absent result.

## Fixture and cache isolation

Lifecycle/installer fixture preparation is immutable and keyed by source tree
digest, Python version and installer catalog digest. Each test obtains a fresh
copy. Git state, environment, locks, Status, Outcome, coverage and target paths
are never shared across tests or shards.

## Verification

Tests cover manifest completeness, skip/xfail changes, wrong-SHA and missing
artifact mutations, statistics, progress cadence, result-schema completeness,
and workflow ownership. Local full quality remains required. Five sequential
Hosted baseline samples and five candidate samples are retained separately in
the active Summary before finalization.
