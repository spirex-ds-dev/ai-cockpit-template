---
author: Ray
title: "User-Facing Capability Guides Implementation Plan"
description: "Detailed implementation instructions for the three-language, natural-language-first AI Cockpit capability documentation update."
keywords:
  - ai-cockpit
  - documentation
  - implementation-plan
  - multilingual
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# User-Facing Capability Guides Implementation Plan

> **Work Item:** `docs-user-facing-guides-20260820`
> **Base:** `7b1ea9760d4d0403b826d4c634832d87e6c6d3a1`
> **Delivery boundary:** documentation only; no release or version change.

## 1. Establish the navigation spine

Update `docs/README.md`, `docs/README.zh-CN.md`, and `docs/README.ja.md` so
the reader can reach the capability map and the four primary journeys from the
existing docs home. Keep the existing five-minute orientation and add a
reader-goal table for:

- understanding what AI Cockpit can claim;
- understanding a completed or blocked result;
- finding prior verified implementation knowledge;
- processing independent Work Items concurrently;
- installing, calibrating, upgrading, recovering, and reading status.

Every route must have an equivalent language sibling or an explicit labelled
English advanced fallback.

## 2. Build the capability overview/index

Update `docs/capabilities.md`, `docs/capabilities.zh-CN.md`, and
`docs/capabilities.ja.md` as the first-class capability overview. Keep it
scannable: it is an index, not a replacement for detailed feature guides.

For each adopter-facing capability, show one row with:

1. the user goal or capability name;
2. the current status (`adopter_installed`, `implemented`, `template_only`, or
   another manifest status);
3. the plain-language value;
4. the boundary or responsible owner;
5. a localized Details link to the focused guide, or an explicit English
   advanced fallback when no localized detail page is authoritative.

The overview must expose direct links for Outcome/Reports, Knowledge, Work Item
parallel processing, lifecycle/status/recovery, installation/calibration, and
upgrade. Keep the detailed prerequisites, examples, stop conditions, and
commands on the linked pages so readers can progressively disclose complexity.

Do not turn this page into a schema catalog. Link to technical references for
commands, JSON fields, and maintainer-only implementation detail.

## 3. Rewrite the outcome journey

Update the English Task Outcome page and add its Chinese and Japanese siblings.
Add or preserve the evidence-bound technical detail, but lead with the user's
question and a natural-language request. Explain the four distinct records:
Contract, Summary, Task Outcome, and Human Benefit Report. Add a problem-to-
resolution example with an evidence reference and a second warning/stop example
showing what the user should do when evidence is missing. Link to the existing
Human Benefit Report pages in all three languages.

Update the existing Human Benefit Report siblings only where needed to make the
same journey discoverable and aligned; retain its concise projection role and
do not duplicate Task Outcome as a second fact source.

## 4. Add the Knowledge journey

Rewrite `docs/reference/implementation-knowledge.md` around the reader's goal,
then add `implementation-knowledge.zh-CN.md` and
`implementation-knowledge.ja.md`. Explain prerequisites, what to say to an AI
assistant, what records are searched, how exact filters combine, what a
validated result looks like, and when to stop. Put the generation, validation,
and query commands after the natural-language path. Preserve the non-semantic,
non-vector, non-RAG and read-only boundaries exactly.

Use examples for a topic/component query, a date-range query, no matches, and a
stale/conflicting evidence case. Link the technical query interface and the
Outcome/Human Benefit Report routes.

## 5. Add the Work Item parallel-processing journey

Create `docs/features/work-item-parallelism.md`,
`work-item-parallelism.zh-CN.md`, and `work-item-parallelism.ja.md`. Explain
parallel Work Item ownership in ordinary language and distinguish it from
parallel verification. Include:

- prerequisites: trusted base, independent goals, separate branch/worktree,
  explicit scope, and no shared mutable evidence;
- natural-language request and expected dispatch/result;
- safe and unsafe examples;
- serialization of shared paths and projections;
- bounded parallel verification limits;
- WIII's read-only current-worktree scope;
- Agent/Orchestrator ownership of scheduling and retry;
- stop/recovery when ownership, evidence, or base synchronization conflicts.

Update the three lifecycle pages to link to this focused guide and retain the
canonical closure rules. Do not imply a new scheduler or runtime feature.

## 6. Close supporting discovery gaps

Add `docs/upgrade.zh-CN.md` by aligning the existing English and Japanese
upgrade routes. Add links from the capability map and each language's reader
goal table. Update lifecycle and capability pages only where a user needs to
move from explanation to action. Avoid translating maintainer-only references
that are not part of the reader journey.

## 7. Refresh generated documentation evidence

After the prose and link map stabilize, regenerate
`docs/reference/capability-truth-matrix.json` using the repository's supported
generator rather than hand-editing generated output. Generate the Work Item
status/report/knowledge projections required by the active lifecycle command,
then inspect the result for language and capability claims. Do not edit
production generators or schemas.

## 8. Verify in layers

Run the focused documentation checks first, then the Work Item checks:

1. Follow all three root/docs entry routes and all new/changed internal links.
2. Compare every localized sibling against the semantic parity checklist:
   goal, prerequisites, natural-language action, example, expected result,
   stop/recovery, boundary, advanced route, related links.
3. Check every manifest capability row and every status/ownership label against
   the manifest and Capability Truth Matrix.
4. Run `make check-docs-metadata`, the configured documentation journey/link
   checks, capability-claim and Japanese-language checks, source-bound evidence,
   and diff checks if available in the repository.
5. Run the Contract's registered checks, including scope, guards, checkpoint,
   agent risk, scenario coverage, guidelines, Summary, status, ownership,
   unsupported claims, and quality.
6. Inspect `git diff --name-only` and `git diff --check`; the changed paths
   must remain in documentation or generated documentation evidence only.
7. Record all results and any explicitly not-run command with a reason in the
   active Summary. No release, tag, version, PR, or provider operation is run.

## 9. Handoff

Keep the Work Item on its dedicated branch for review. The handoff must include
the changed documentation entry points, the three-language parity result, the
capability-claim result, and the verification evidence. A later PR/merge/release
decision is outside this documentation implementation plan and requires its own
authorization.
