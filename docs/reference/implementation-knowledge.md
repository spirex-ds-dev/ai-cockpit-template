---
author: Ray
title: "Implementation Knowledge"
description: "A natural-language-first guide to finding validated, archive-derived Work Item implementation knowledge."
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - implementation_knowledge_query
  - implementation_knowledge_projection
keywords:
  - ai-cockpit
  - implementation-knowledge
  - evidence-bound
  - work-item
---

# Implementation Knowledge

## What this helps you do

Use Knowledge when you want to learn from a previous governed change. For
example: “Which verified Work Item addressed the order service, and what files
and evidence did it leave?” The result is a deterministic lookup over validated
implementation records, not a confident-sounding answer from Agent memory.

## Before you start

Knowledge records are created from completed Work Item evidence. The Contract,
Summary, repository evidence, and final Outcome remain authoritative. If a
Work Item has not reached a usable Outcome, or its record is missing or stale,
there may be no verified result to return.

## How records are refreshed

When a Work Item is finalized, AI Cockpit maintains three generated views:
the Knowledge records, the query index, and a dependency map. The dependency
map records which Contract, Summary, Outcome, and Evidence paths determine each
record, then maps a changed path to the affected Work Items.

On the normal Finish or Archive path, that map lets AI Cockpit refresh the
current record and the affected historical records only. An unrelated record
is not normally rebuilt or rewritten, and a generated file is replaced only
when its serialized content changes.

This is a maintenance boundary, not a promise that every recovery is cheap. If
the dependency map is missing, malformed, stale, or incomplete, AI Cockpit
performs an explicit full rebuild/revalidation or stops fail closed. A full
recovery may inspect more historical records, so maintenance time and
governance cost can grow as the Knowledge history grows. The query itself stays
read-only; if a refresh stops, inspect the checker result and repair the
evidence before reusing a record.

## Ask in ordinary language first

You can ask your Agent:

> “Find verified Work Items about orders that affected the OrderService
> component. Show the Work Item ID, state, evidence paths, and what I should
> inspect next.”

The Agent may translate that request into exact filters. AI Cockpit does not
pretend that it understands arbitrary natural-language meaning inside the
query engine: the underlying interface is structured, read-only, and
conjunctive. The human-facing sentence is the HCI entry; the exact filter and
the returned record are the evidence boundary.

## What happens

1. The Agent identifies the topic, component, date, commit, Work Item, or state
   filters that the request actually names.
2. The query reads the validated index and matching Knowledge records.
3. Every record is checked against its source paths and frozen SHA-256 digests.
4. Results are returned in stable Work Item ID and knowledge-path order.
5. You inspect the record's evidence and limitations before reusing the design.

Filters combine with **AND** semantics. Supported filters are Work Item ID,
topic, component, merged commit, exact date, inclusive date range, and
Knowledge state (`verified`, `partial`, `unknown`, `superseded`).

## Example: a useful result

Request:

> “Show me verified order-service changes from January 2026.”

Expected result:

```text
Query: topic=orders, component=OrderService, date-from=2026-01-01,
       date-to=2026-01-31, status=verified
Matches: 1
Next: open the returned knowledgePath and its evidenceRefs before applying
      the design to a new Work Item.
```

If the result is empty, that means no record matched all named filters. It does
not mean the repository has never addressed the topic. Broaden one exact
filter intentionally, or ask a person to identify a different evidence source.

If a record is stale, malformed, conflicting, or has an invalid supersession
relationship, validation fails closed or keeps the record visibly partial or
unknown. Do not silently select the newest-looking file.

## What Knowledge does not do

Knowledge is not:

- semantic, vector, fuzzy, or RAG search;
- a relevance scorer, recommendation engine, or design authority;
- a second fact source that can overrule Contract, Summary, Outcome, or source
  evidence;
- a writer: queries do not modify records, indexes, reports, or Work Items;
- a guarantee that an archived implementation still fits a new repository.

Dates are used only when explicitly present in Contract, Summary, or Outcome.
The system does not guess dates from file timestamps or commit history.
Supersession is taken from an explicit relationship; it is never inferred from
similarity. Legacy records may remain `partial`.

## Advanced route

After the source Summary and Outcome are complete, generate or rebuild records:

```sh
make ai-generate-knowledge \
  TASK=<work-item-id> \
  CONTRACT=.ai/work-items/active/<work-item-id>.contract.json \
  SUMMARY=.ai/work-items/active/<work-item-id>.summary.json \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

Validate the records and indexes:

```sh
make ai-check-knowledge-index
make check-ai-knowledge
```

Query with exact filters:

```sh
make ai-knowledge-query TOPIC=orders COMPONENT=OrderService STATUS=verified
make ai-knowledge-query DATE_FROM=2026-01-01 DATE_TO=2026-01-31
```

The JSON result includes a normalized query, match count, stable `results`,
and the compatibility alias `matches`. Each result exposes `workItemId`,
`knowledgePath`, `state`, `latestKnownRecord`, `supersessionStatus`, and the
complete record.

## Stop and related entry points

Stop when evidence is missing, stale, contradictory, or outside the record's
declared sources. Ask for a new evidence-bound Work Item rather than filling
the gap from memory.

- [Task Outcome Report](../features/task-outcome-report.md)
- [Human Benefit Report](../features/human-benefit-report.md)
- [Capabilities and boundaries](../capabilities.md)
- [Work Item Lifecycle](../operations/work-item-lifecycle.md)
