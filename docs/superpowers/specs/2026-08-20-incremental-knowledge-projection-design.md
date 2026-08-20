---
author: Ray
title: "Incremental Knowledge Projection"
description: "Bounded design for dependency-aware Implementation Knowledge projection refresh."
authority: supporting
audience:
  - maintainer
  - reviewer
keywords:
  - ai-cockpit
  - implementation-knowledge
  - dependency-index
  - incremental-projection
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# Incremental Knowledge Projection

## Problem

`rebuild_existing_projections()` currently visits every existing Knowledge
Record after shared source-bound evidence changes. It avoids rewriting a
serialized Record whose content is unchanged, but it still loads every Record,
resolves its archived sources, hashes its Contract/Summary/Outcome and
Evidence, and compares the rebuilt payload. The normal lifecycle cost therefore
grows with historical Knowledge volume.

The goal is to preserve the existing Evidence-bound truth model while making
ordinary unrelated Work Item finalization independent of unrelated historical
Record contents.

## Boundaries and non-goals

- Contract, Summary, Outcome, repository Evidence, and explicit lifecycle facts
  remain authoritative. Knowledge remains a generated projection.
- The query interface remains deterministic exact-AND lookup. This design adds
  no semantic search, embeddings, vector storage, LLM ranking, or customer
  answer generation.
- The implementation uses repository-local JSON only. It adds no database,
  cache server, daemon, or external service.
- Archived Contract, Summary, Outcome, archive manifest, and archive index
  bytes remain immutable.

## Data model

Add `.ai/knowledge/dependencies.json` as a generated reverse dependency
projection. Its conceptual shape is:

```json
{
  "schemaVersion": 1,
  "records": {
    "work-item-id": {
      "recordPath": ".ai/knowledge/work-items/work-item-id.json",
      "dependencies": [
        ".ai/work-items/archive/2026/work-item-id.contract.json",
        "tests/example.py"
      ]
    }
  },
  "byPath": {
    "tests/example.py": ["work-item-id"]
  }
}
```

Each Record dependency set is derived from its `generatedFrom` Contract,
Summary, and Outcome paths plus every projected Evidence path. The reverse
mapping is sorted and de-duplicated, so the same inputs produce the same file.

The existing `index.json` remains the query index. Its update path gains an
incremental entry operation; it is not repurposed as a dependency registry.

## Lifecycle behavior

### New Record

When a new Work Item is generated, build only that Record. Update its one
`index.json` entry and one `dependencies.json` record/reverse mapping. Existing
Records are not opened, hashed, or rewritten.

### Shared Evidence refresh

The Finish source-bound refresh already knows which generated repository paths
were processed. It passes those changed paths to the projection refresher:

```text
changed generated paths
        ↓
dependencies.byPath[path]
        ↓
affected Work Item IDs
        ↓
rebuild affected archived Records only
        ↓
incrementally update index and dependency projection
```

An empty changed-path set updates only explicitly requested current Record IDs.
The Archive path uses this behavior after generating the just-archived Record.

### Missing or invalid dependency projection

If `dependencies.json` is absent, malformed, structurally inconsistent, or
cannot provide a trustworthy affected set, the refresher does not reuse old
Records silently. It performs one explicit full rebuild and reconstructs both
indexes, or fails closed when an archived source is missing, ambiguous, or
invalid. The fallback is observable in the returned detail and Summary
verification evidence.

The full checker remains the authoritative audit path: it validates every
Record, every query-index entry, and every dependency-index relationship.

## Interfaces

The generator module exposes these bounded operations:

- `dependency_paths(record)` returns the normalized dependency paths for one
  generated Record.
- `rebuild_index(records_dir, output_path, *, record_updates=None,
  full=False)` updates only named entries in the normal path and retains a
  full deterministic rebuild mode for recovery.
- `rebuild_dependency_index(records_dir, output_path, *, record_updates=None,
  full=False)` maintains the reverse mapping with the same recovery boundary.
- `rebuild_existing_projections(repo_root, *, changed_paths=None,
  include_work_item_ids=())` routes to affected archived Records, performs the
  explicit full fallback when dependency proof is unavailable, and returns
  only paths whose serialized bytes changed.

The lifecycle callers pass changed generated paths explicitly. The standalone
generator command remains compatible and treats its current Record as the only
normal update.

## Error handling and safety

- All repository-relative dependency paths are normalized and must remain
  inside the repository.
- Duplicate Record identities, missing target Records, malformed reverse
  mappings, and dependency mismatches fail closed in the checker.
- Atomic writes are retained, and a file is replaced only when serialized
  content differs.
- Query behavior and current-validity unknown preservation are unchanged.

## Verification strategy

The regression suite proves new-record, affected-record, unaffected-record,
missing-dependency, archive/Finish, PR-boundary, and fresh-adopter behavior.
The complexity benchmark builds synthetic dependency mappings for 1,000 and
10,000 Records, records local timings, and counts routed affected IDs. The
invariant is that an unrelated refresh does not inspect or rebuild all Record
contents; wall-clock values remain environment-bound supporting evidence.
