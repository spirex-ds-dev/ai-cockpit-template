---
author: Ray
title: "Documentation Criticality Registry Implementation Plan"
description: Test-first delivery plan for documentation authority registry v2 and multilingual reader-journey gates.
status: historical
authority: implementation_record
---

# Documentation Criticality Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

**Goal:** Deliver WI-1 of the multilingual documentation initiative: a backward-compatible documentation authority registry v2, explicit P0/P1/P2 topic inventory, migration state, and executable coverage and localized-navigation policy.

**Architecture:** Extend `docs/reference/documentation-authority-registry.json` instead of creating a competing registry. Keep agent read-set behavior isolated in `scripts/ai_documentation_authority.py`; add a focused `scripts/ai_documentation_journey.py` module for reader-topic coverage and graph validation, then integrate both through the existing documentation metadata gate and Make entrypoints.

**Tech Stack:** Python 3.11 standard library, JSON, Markdown link parsing, pytest, GNU Make-compatible repository targets.

## Global Constraints

- This plan implements registry and verification policy only; it does not rewrite or translate product documentation.
- P0 requires English, Japanese, and Simplified Chinese when a topic becomes `active`.
- `planned` P0 topics expose migration gaps but do not claim coverage or block unrelated work.
- An `active` topic cannot be downgraded to `planned`.
- P1 may use an explicitly labelled English technical fallback; P2 has no default translation requirement.
- One topic has one canonical semantic owner.
- Existing `make ai-documentation-read-set` output remains backward compatible.
- Use the repository-resolved Make entrypoint and the full AI Cockpit Work Item lifecycle.
- Every implementation task uses test-first development and ends with a focused commit.

---

## Delivery boundary

Create a new `MODE=code` Work Item after this design Work Item is reviewed,
merged, and closed. Use a task name such as
`documentation-criticality-registry-v2`. Its Contract must own only the files
listed in this plan plus generated Work Item evidence.

Do not begin WI-2 localized documentation homes on the WI-1 branch.

## File map

- Modify `docs/reference/documentation-authority-registry.json`: upgrade to
  schema version 2 and declare the intended reader-topic inventory.
- Modify `scripts/ai_documentation_authority.py`: validate v1/v2 authority
  records while preserving the existing agent read-set query.
- Create `scripts/ai_documentation_journey.py`: validate topic criticality,
  locales, migration state, semantic ownership, next-topic graph, localized
  routes, and fallback labels.
- Modify `scripts/check_docs_metadata.py`: call the journey validator as part
  of repository documentation checks.
- Modify `tests/test_documentation_authority.py`: cover registry v2 and v1
  compatibility.
- Create `tests/test_documentation_journey.py`: focused positive and negative
  tests for topic and graph policy.
- Modify `tests/test_docs_metadata.py`: prove the public metadata gate includes
  the journey result.
- Modify `Makefile`: expose a focused documentation-journey check target and
  include it in the documented check surface without duplicating execution
  inside `quality`.
- Modify `docs/reference/documentation-authority-boundary.md`: document v2
  authority versus reader-journey responsibilities and migration semantics.
- Modify `docs/reference/documentation-architecture.md`: describe P0/P1/P2 and
  point maintainers to the registry without claiming P0 migration is complete.

### Task 1: Freeze v2 data contracts in tests

**Files:**

- Modify: `tests/test_documentation_authority.py`
- Create: `tests/test_documentation_journey.py`

**Interfaces:**

- Consumes: current `validate_registry(registry: object) -> list[str]` and
  `query_records(registry, include_reference=False) -> list[dict]`.
- Produces: fixture helpers `v1_registry() -> dict[str, object]` and
  `v2_registry() -> dict[str, object]` used by later tasks.

- [ ] **Step 1: Rename the current fixture helper**

Rename `registry()` to `v1_registry()` and update its three call sites. Do not
change its data or existing assertions.

- [ ] **Step 2: Add a v2 authority fixture and failing compatibility test**

Add `v2_registry()` by copying the v1 authority documents, setting
`schemaVersion` to `2`, and adding a `topics` list containing one active P0
topic with `en`, `ja`, and `zh-CN` paths. Assert that `validate_registry()`
returns no errors and that `query_records()` returns the same default agent
read set for v1 and v2.

- [ ] **Step 3: Run the compatibility test and observe failure**

Run:

```sh
PYTHONPATH=scripts .venv/bin/pytest -q tests/test_documentation_authority.py
```

Expected: the new v2 test fails with `registry schemaVersion must be 1`.

- [ ] **Step 4: Add reader-topic fixture shape**

Create `tests/test_documentation_journey.py` with a `topic_registry()` helper
whose topic contains these exact fields:

```python
{
    "topic": "product-architecture",
    "criticality": "P0",
    "canonicalPath": "docs/architecture.md",
    "localizedPaths": {
        "en": "docs/architecture.md",
        "ja": "docs/architecture.ja.md",
        "zh-CN": "docs/architecture.zh-CN.md",
    },
    "audiences": ["adopter"],
    "journeys": ["understand"],
    "nextTopics": [],
    "enforcementStatus": "active",
    "plainLanguageRequired": True,
    "semanticInvariants": ["external-controls-remain-external"],
}
```

Add failing imports for `validate_topics` and `validate_journeys` from
`scripts.ai_documentation_journey`.

- [ ] **Step 5: Run the new test module and observe failure**

Run:

```sh
PYTHONPATH=. .venv/bin/pytest -q tests/test_documentation_journey.py
```

Expected: collection fails because `scripts.ai_documentation_journey` does not
exist.

- [ ] **Step 6: Commit the red tests**

```sh
git add tests/test_documentation_authority.py tests/test_documentation_journey.py
git commit -m "test(docs): define documentation registry v2 contract"
```

### Task 2: Add backward-compatible authority registry v2 validation

**Files:**

- Modify: `scripts/ai_documentation_authority.py`
- Test: `tests/test_documentation_authority.py`

**Interfaces:**

- Consumes: registry schema versions `1` and `2`.
- Produces: unchanged `query_records()` behavior and a `validate_registry()`
  result that delegates v2 topic validation without changing the agent read
  set.

- [ ] **Step 1: Accept schema versions 1 and 2**

Replace the fixed version comparison with membership in `{1, 2}`. Keep the
stable error `registry schemaVersion must be 1 or 2` for every other value.

- [ ] **Step 2: Require topics only for version 2**

For v2, require `topics` to be a list. For v1, reject a `topics` property so a
partially upgraded registry cannot be mistaken for v2.

- [ ] **Step 3: Keep query behavior authority-only**

Do not make `query_records()` return reader topics. The CLI's existing default
and `--include-reference` output must remain byte-shape compatible.

- [ ] **Step 4: Run authority tests**

```sh
PYTHONPATH=scripts .venv/bin/pytest -q tests/test_documentation_authority.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```sh
git add scripts/ai_documentation_authority.py tests/test_documentation_authority.py
git commit -m "feat(docs): accept authority registry schema v2"
```

### Task 3: Implement topic validation and migration safety

**Files:**

- Create: `scripts/ai_documentation_journey.py`
- Test: `tests/test_documentation_journey.py`

**Interfaces:**

- Produces:
  `validate_topics(registry: Mapping[str, Any], root: Path) -> list[str]`.
- Produces:
  `topic_index(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]`.
- Valid values: criticality `P0|P1|P2`; enforcement status
  `planned|active`; locales `en|ja|zh-CN`.

- [ ] **Step 1: Add failing malformed-topic cases**

Cover duplicate topic IDs, invalid criticality, missing canonical path, invalid
locale keys, missing P0 locales, invalid enforcement status, missing referenced
files for active topics, and duplicate canonical owners.

- [ ] **Step 2: Add planned-versus-active cases**

Assert that a planned P0 topic may name paths that do not yet exist and returns
a structured warning from `planned_gaps()` but no blocking error from
`validate_topics()`. Assert that the same missing paths block when the topic is
active.

- [ ] **Step 3: Implement pure validation**

Use only `collections.abc.Mapping`, `pathlib.Path`, and standard-library types.
Return deterministic, path-qualified messages sorted by topic and field. Do not
write files or mutate the registry.

- [ ] **Step 4: Implement visible planned gaps**

Add:

```python
def planned_gaps(registry: Mapping[str, Any], root: Path) -> list[dict[str, str]]:
    """Return non-passing migration gaps for planned topics."""
```

Each record contains `topic`, `locale`, `path`, and `reason`. Empty paths and
missing files are both reported.

- [ ] **Step 5: Run focused tests**

```sh
PYTHONPATH=. .venv/bin/pytest -q tests/test_documentation_journey.py -k "topic or planned"
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```sh
git add scripts/ai_documentation_journey.py tests/test_documentation_journey.py
git commit -m "feat(docs): validate criticality and migration state"
```

### Task 4: Implement localized journey graph validation

**Files:**

- Modify: `scripts/ai_documentation_journey.py`
- Modify: `tests/test_documentation_journey.py`

**Interfaces:**

- Produces:
  `validate_journeys(registry: Mapping[str, Any], root: Path) -> list[str]`.
- Produces:
  `markdown_links(path: Path) -> list[tuple[str, str]]`, returning link label
  and target for ordinary inline Markdown links.
- Consumes: registered `nextTopics`, localized paths, and localized root README
  topic entries.

- [ ] **Step 1: Add failing graph cases**

Create temporary Markdown fixtures for: unknown next topic, stranded active P0
topic, wrong-language next link, language switch to a different topic, P0 topic
more than two links from the localized entry, current route into
`docs/archive/`, and an unlabelled P1 English fallback.

- [ ] **Step 2: Add passing graph cases**

Cover a complete three-language P0 chain and a Japanese P1 summary whose link
label ends in `— English`.

- [ ] **Step 3: Implement Markdown link extraction**

Resolve relative `.md` targets against the source page. Ignore external URLs,
anchors on the same page, images, and links inside fenced code blocks. Strip
fragment identifiers before filesystem and topic matching.

- [ ] **Step 4: Implement graph traversal**

For each locale, breadth-first traverse registered current routes from the
localized documentation-home topic. Active P0 topics must be reachable in at
most two edges. Validate declared next-topic links against the same locale.

- [ ] **Step 5: Implement explicit P1 fallback rule**

Allow a P1 localized page to target the English canonical path only when the
link label contains the exact visible language token `English`. Do not apply
this exception to P0.

- [ ] **Step 6: Run journey tests**

```sh
PYTHONPATH=. .venv/bin/pytest -q tests/test_documentation_journey.py
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```sh
git add scripts/ai_documentation_journey.py tests/test_documentation_journey.py
git commit -m "feat(docs): validate localized documentation journeys"
```

### Task 5: Upgrade and inventory the repository registry

**Files:**

- Modify: `docs/reference/documentation-authority-registry.json`
- Test: `tests/test_documentation_authority.py`
- Test: `tests/test_documentation_journey.py`

**Interfaces:**

- Consumes: v2 schema validated by Tasks 2–4.
- Produces: complete intended P0 topic inventory, with existing complete
  trilingual topics active and incomplete topics planned.

- [ ] **Step 1: Upgrade the registry version**

Set `schemaVersion` to `2` and preserve the existing three authority documents
unchanged.

- [ ] **Step 2: Add all fourteen P0 topic identifiers from the design**

Use stable lowercase hyphenated IDs. Register existing canonical paths where
they exist. For missing localized paths, record the intended final path and set
the topic to `planned`.

- [ ] **Step 3: Register P1 and P2 policy representatives**

Register command reference and schema reference as P1. Register the
documentation design and plan families as P2 patterns only if the validator
supports patterns explicitly; otherwise register their current entry pages and
leave individual historical records governed by the context registry.

- [ ] **Step 4: Verify no false completeness claim**

Run the CLI report and assert that every incomplete P0 topic appears under
`plannedGaps`, while active topics have no missing locale or path.

- [ ] **Step 5: Commit**

```sh
git add docs/reference/documentation-authority-registry.json tests/test_documentation_authority.py tests/test_documentation_journey.py
git commit -m "docs(governance): inventory documentation criticality"
```

### Task 6: Integrate the public checks

**Files:**

- Modify: `scripts/check_docs_metadata.py`
- Modify: `tests/test_docs_metadata.py`
- Modify: `Makefile`

**Interfaces:**

- Produces: `documentation_journey_errors(root: Path) -> list[str]` in
  `check_docs_metadata.py`.
- Produces: a focused public Make target for the documentation-journey checker.
- Preserves: `make check-docs-metadata` as the aggregate documentation gate.

- [ ] **Step 1: Add a failing aggregate-gate test**

Copy repository documentation to `tmp_path`, remove one active P0 Japanese
file, and assert `check_repository(tmp_path)` includes the journey error.

- [ ] **Step 2: Add a focused CLI entrypoint**

In `ai_documentation_journey.py`, add `--registry`, `--root`, `--check`, and
`--format json`. On invalid active policy return exit code `2`; on success
return `0` and include planned gaps without calling them passed.

- [ ] **Step 3: Integrate metadata validation**

Load the authority registry once, append v2 topic and journey errors to
`check_repository()`, and keep v1 repositories valid with no reader-topic
checks.

- [ ] **Step 4: Add the Make target**

Define a target named from the script's purpose that dispatches:

```make
documentation-journey-check:
	$(AI_PYTHON) scripts/ai_documentation_journey.py --check
```

Add it to `.PHONY` and Make help. Do not add a second invocation to the same
quality aggregate when `check-docs-metadata` already runs it.

- [ ] **Step 5: Run focused integration tests**

```sh
PYTHONPATH=scripts:. .venv/bin/pytest -q tests/test_docs_metadata.py tests/test_documentation_authority.py tests/test_documentation_journey.py
make check-docs-metadata
```

Expected: all commands pass and the focused check visibly reports planned P0
gaps as incomplete migration, not success.

- [ ] **Step 6: Commit**

```sh
git add Makefile scripts/ai_documentation_journey.py scripts/check_docs_metadata.py tests/test_docs_metadata.py tests/test_documentation_journey.py
git commit -m "feat(docs): gate documentation journey integrity"
```

### Task 7: Document the policy without claiming migration completion

**Files:**

- Modify: `docs/reference/documentation-authority-boundary.md`
- Modify: `docs/reference/documentation-architecture.md`

**Interfaces:**

- Consumes: implemented v2 fields and CLI behavior.
- Produces: maintainer guidance for authority, criticality, migration, and
  recovery.

- [ ] **Step 1: Update the authority boundary**

Explain that authority answers “which document may instruct or own truth,”
while criticality answers “which reader journey and locales are mandatory.”
Document v1 read compatibility and v2 write policy.

- [ ] **Step 2: Update documentation architecture**

Add P0/P1/P2 definitions, `planned` versus `active`, prohibition on active
downgrades, and the rule that planned gaps cannot support a multilingual
completeness claim.

- [ ] **Step 3: Run documentation checks**

```sh
make check-docs-metadata
make ai-documentation-read-set
```

Expected: metadata passes; the default read set remains only the canonical
agent route.

- [ ] **Step 4: Commit**

```sh
git add docs/reference/documentation-authority-boundary.md docs/reference/documentation-architecture.md
git commit -m "docs(governance): explain reader journey policy"
```

### Task 8: Complete governed verification

**Files:**

- Modify: active Work Item Contract and Summary
- Generate: repository-governed status and Outcome artifacts

**Interfaces:**

- Consumes: all WI-1 commits.
- Produces: review-ready evidence without starting WI-2.

- [ ] **Step 1: Run focused tests once more**

```sh
PYTHONPATH=scripts:. .venv/bin/pytest -q tests/test_documentation_authority.py tests/test_documentation_journey.py tests/test_docs_metadata.py
```

- [ ] **Step 2: Run the new and existing public checks**

```sh
make check-docs-metadata
make ai-documentation-read-set
```

- [ ] **Step 3: Update Summary evidence**

Record every changed file, focused result, planned P0 gap, migration limitation,
guideline result, and the explicit fact that localized content was not changed.

- [ ] **Step 4: Run the Contract's complete Finish sequence**

Use the current repository Make entrypoint and exact active Contract/Summary.
Run the required `before_finish` checkpoint, every Contract verification item,
status generation and consistency, then run:

```sh
make ai-finish TASK=documentation-criticality-registry-v2
```

- [ ] **Step 5: Stop at review readiness**

Do not begin WI-2 on this branch. Push, PR, merge, and close the Work Item only
with the authorization and provider workflow required by the repository.
