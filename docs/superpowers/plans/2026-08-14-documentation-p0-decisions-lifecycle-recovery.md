---
author: Ray
title: "Documentation P0 Decisions, Lifecycle, and Recovery Implementation Plan"
description: "Implementation record for the WI-4 trilingual decision journey."
status: historical
authority: implementation_record
---

# Documentation P0 Decisions, Lifecycle, and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

**Goal:** Make decision states, Cockpit status, Work Item lifecycle, stop conditions, and recovery understandable and safe in English, Japanese, and Simplified Chinese.

**Architecture:** Keep one canonical semantic owner per P0 topic and add localized siblings beside the existing canonical pages. The pages share a reader-first structure, while the registry and focused tests enforce locale parity, same-language navigation, explicit human decisions, and no-guessing stop conditions.

**Tech Stack:** Markdown, JSON, Python standard library, pytest, GNU Make-compatible documentation gates.

## Global Constraints

- This Work Item changes documentation, registry state, and documentation tests only; it does not change runtime lifecycle behavior.
- WI-4 owns only decision states, status interpretation, lifecycle/stop conditions, and recovery overview; installation, calibration, first Work Item, adoption, and security remain successor P0 Work Items.
- Every active WI-4 P0 topic has English, Japanese, and Simplified Chinese semantic siblings.
- Green, Yellow, Red, and Unknown remain machine-stable meanings: proceed, review/limited risk, stop/intervention, and evidence insufficiency.
- A stop condition must state the reason, the human decision, the safe next action, and the forbidden guess or bypass.
- Do not silently fall back to English on the WI-4 P0 route.

---

## File Map

- Modify `docs/reference/documentation-authority-registry.json` to activate the WI-4 topics and preserve planned successor topics.
- Modify `docs/README.md`, `docs/README.ja.md`, and `docs/README.zh-CN.md` to expose the same-language WI-4 journey.
- Modify root `README.md`, `README.ja.md`, and `README.zh-CN.md` only where the canonical journey link is missing or stale.
- Create localized siblings for `docs/concepts/decision-states.md`, `docs/reference/how-to-read-cockpit-status.md`, `docs/operations/work-item-lifecycle.md`, and `docs/operations/recovery.md`.
- Create `tests/test_documentation_p0_decisions_lifecycle_recovery.py` for structural, semantic, registry, and route invariants.

## Task 1: Freeze the WI-4 acceptance fixtures

**Files:**

- Create: `tests/test_documentation_p0_decisions_lifecycle_recovery.py`
- Test: existing English canonical pages and registry

- [ ] Add fixtures for the required P0 section order and the status/action semantic vocabulary.
- [ ] Add failing tests for the four topic IDs, all three locale paths, and active registry state.
- [ ] Add failing tests for same-language next links and no English fallback in Japanese/Chinese routes.
- [ ] Add failing tests for required stop-condition phrases: reason, human decision, safe next action, and do-not-guess boundary.
- [ ] Run `PYTHONPATH=. pytest -q tests/test_documentation_p0_decisions_lifecycle_recovery.py` and record the expected failures.

## Task 2: Write the four trilingual P0 pages

**Files:**

- Create/modify the 12 locale pages under `docs/concepts/`, `docs/reference/`, and `docs/operations/`.

- [ ] Rewrite each English owner with the nine-section P0 order: Purpose, Audience, Outcome, Scenario, Explanation, Action or decision, Stop conditions, Next steps, Technical depth.
- [ ] Add Japanese siblings preserving the same topic identity, status meanings, stop conditions, and next-topic order.
- [ ] Add Simplified Chinese siblings preserving the same topic identity, status meanings, stop conditions, and next-topic order.
- [ ] Make every status explain the human decision and next safe action; explicitly state that Unknown evidence is not permission to guess.
- [ ] Run the focused structural tests and correct any section, semantic, or link failure.

## Task 3: Repair same-language journey and registry ownership

**Files:**

- Modify: `docs/README.md`, `docs/README.ja.md`, `docs/README.zh-CN.md`
- Modify: `README.md`, `README.ja.md`, `README.zh-CN.md` when required by route tests
- Modify: `docs/reference/documentation-authority-registry.json`

- [ ] Add the four WI-4 topics to each localized home in the core journey order.
- [ ] Set `decision-states`, `lifecycle`, and `recovery` to `active` only after all required locale files exist; keep `how-to-read-cockpit-status` under its canonical topic relationship without duplicating ownership.
- [ ] Preserve the registry's active topics and planned successor topics; do not downgrade an active topic.
- [ ] Run `make check-docs-metadata` and `make documentation-journey-check`.

## Task 4: Verify safety and comprehension boundaries

- [ ] Run `PYTHONPATH=. pytest -q tests/test_documentation_p0_decisions_lifecycle_recovery.py tests/test_documentation_p0_core.py tests/test_documentation_homes.py tests/test_documentation_journey.py tests/test_docs_metadata.py`.
- [ ] Run the Japanese capability and pre-release documentation alignment generators/checks required by the Contract.
- [ ] Record scenario evidence in the Summary: one status interpretation walkthrough and one stop/recovery walkthrough per locale.
- [ ] Run `make ai-finish TASK=documentation-p0-decisions-lifecycle-recovery` and resolve every required check before archiving.
- [ ] Commit the archive bundle, run `make check-ai-pr AI_BASE_COMMIT=837bf320652b000f3d7ed2796ed9ed51a93dc2c0`, then push and open the single PR.

## Acceptance Review

- [ ] A non-technical reader can distinguish proceed, review, investigate, stop, and unknown states in all three locales.
- [ ] A stopped Work Item route tells the reader why it stopped, who decides, what safe action follows, and what must not be guessed or bypassed.
- [ ] All WI-4 P0 routes are reachable within two links from the matching localized documentation home with no silent language switch.
- [ ] The registry, pages, tests, Summary, and generated evidence describe the same bounded topic ownership.
