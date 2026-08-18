---
author: Ray
title: "Implementation Knowledge Projection"
description: "Evidence-bound projection of Work Item implementation knowledge for customer-facing explanation and deterministic lifecycle validation."
audience:
  - adopter
  - reviewer
  - maintainer
authority: implementation_record
keywords:
  - ai-cockpit
  - implementation-knowledge
  - evidence-bound
  - work-item
---

# Implementation Knowledge Projection

AI Cockpit records what changed in the Work Item Summary and explains the
result through Task Outcome and Human Report. The implementation knowledge
projection adds a deterministic, evidence-bound view of how the change works.

## Authority and lifecycle

The projection is derived from existing evidence. The Contract, Summary,
repository evidence, and final Outcome remain authoritative; a knowledge
record is not a second fact source and must not be completed from agent memory
or inferred from a diff.

After a Work Item reaches its final Outcome, generate:

- `.ai/knowledge/work-items/<work-item-id>.json`
- `.ai/knowledge/index.json`

The record keeps the customer-facing implementation summary, mechanism,
affected components, design decisions, changes, effects, evidence paths, and
source digests. The index contains only deterministic lookup fields and does
not perform semantic search or assign relevance scores.

## Evidence rules

Every verified implementation claim must be supported by a repository-relative
evidence path. The generator freezes a SHA-256 digest for each evidence path
and for the Contract, Summary, and Outcome sources. The checker reports stale
or missing paths and source drift. A record with missing or conflicting facts
cannot remain `verified`.

Legacy Work Items remain readable as `partial` records. Missing Implementation
Approach fields become `unknown`; the projection never backfills them.

Knowledge states are `verified`, `partial`, `unknown`, and `superseded`.
`superseded` is reserved for an explicit later Work Item relationship, not an
inference based on similarity.

## Commands

Generate or rebuild a record and index after the source Summary and Outcome are
complete:

```sh
make ai-generate-knowledge-record \
  TASK=<work-item-id> \
  CONTRACT=.ai/work-items/active/<work-item-id>.contract.json \
  SUMMARY=.ai/work-items/active/<work-item-id>.summary.json \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

Validate all records and the deterministic index:

```sh
make ai-check-knowledge-index
```

Query the validated records with exact, conjunctive filters:

```sh
make ai-knowledge-query ARGS='--topic orders --component OrderService --status verified'
make ai-knowledge-query ARGS='--date-from 2026-01-01 --date-to 2026-01-31'
```

The query result is JSON with a schema version, the normalized query, a match
count, and the complete matching records. Results are sorted by Work Item ID
and knowledge path, so the same validated inputs produce the same output.
Supported filters are Work Item ID, topic, component, merged commit, exact
date, inclusive date range, and knowledge state. The filters are exact and
combine with AND semantics. All four knowledge states remain queryable;
supersession is returned from the explicit `supersedes` relationship and is
never inferred.

Dates are filterable only when a record contains an explicit `date` field. The
interface never guesses a date from file timestamps, commit history, or other
metadata. Invalid or missing index/record evidence fails closed, and the
interface is read-only: it does not write records, indexes, or reports. It is
intentionally a deterministic structured lookup, not a natural-language,
semantic, vector, or RAG query layer.

Validate the installed query surface as well as the knowledge index:

```sh
make check-ai-knowledge
```
