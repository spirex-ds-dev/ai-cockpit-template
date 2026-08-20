---
author: Ray
title: "User-Facing Capability Guides Design"
description: "Design for discoverable, natural-language-first AI Cockpit capability documentation in English, Simplified Chinese, and Japanese."
keywords:
  - ai-cockpit
  - documentation
  - multilingual
  - hci
  - work-item
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

# User-Facing Capability Guides Design

## Decision

Add a reader-first capability route to the existing documentation home and
rewrite the high-value capability pages as three-language user journeys. The
reader starts with a goal in ordinary language, sees what AI Cockpit will and
will not do, follows a concrete example, and only then reaches commands,
paths, schemas, or maintainer references as optional advanced detail.

This Work Item changes documentation and generated documentation evidence only.
It does not change runtime behavior, Work Item scheduling, Knowledge query
semantics, reporting schemas, installer behavior, versions, releases, tags,
provider state, or pull requests.

## Reader journey

The navigation graph is intentionally shallow:

```text
README → docs/README → Capabilities and boundaries
                         ├─ Outcome / Summary / Human Benefit Report
                         ├─ Knowledge
                         ├─ Work Item parallel processing
                         ├─ lifecycle, status, recovery, quality gates
                         └─ installation, calibration, upgrade
```

Every localized entry page exposes the same graph with the corresponding
language sibling. Existing technical references remain available and are
labelled as advanced or English-only where no localized page is authoritative.

## Capability overview as the index

`docs/capabilities.md` and its localized siblings are the capability overview,
not another long-form feature manual. They are the first click after the docs
home and provide a scannable map. Each row answers four questions:

| Overview field | Reader question |
| --- | --- |
| Capability / goal | What can I ask AI Cockpit to help with? |
| Current status | Can I use it here, or is it template-only, planned, or external? |
| Boundary / owner | What does AI Cockpit cover, and who owns the rest? |
| Details | Where do I read the natural-language steps, example, stop conditions, and advanced route? |

The overview links to focused detail pages rather than duplicating their full
content. At minimum it links to the Outcome/Reports, Knowledge, Work Item
parallel processing, lifecycle/status/recovery, installation/calibration, and
upgrade journeys. A capability without a dedicated localized detail page must
use an explicit English advanced fallback label. The overview itself remains
short enough to scan in one sitting.

## Page contract

Each user-facing guide uses the following semantic sections, in this order
unless the subject requires a small variation:

1. **What this helps you do** — the user goal and the value of the capability.
2. **Before you start** — the Work Item, installation, evidence, or human
   decision prerequisites.
3. **Tell AI Cockpit what you want** — a natural-language request in the
   reader's terms; no command is required for the primary path.
4. **What AI Cockpit does** — the bounded repository-local behavior and who owns
   any external or scheduling work.
5. **Example** — a realistic request, the expected response/result, and the
   next safe decision.
6. **If it stops, warns, or cannot answer** — red/yellow/unknown behavior,
   recovery action, and the condition that must remain visible.
7. **Boundaries** — what the capability does not prove, schedule, infer, or
   change.
8. **Advanced route** — exact commands, paths, schemas, and maintainer
   references, disclosed only after the natural-language path.
9. **Related entry points** — localized sibling, capability map, and the next
   relevant reader journey.

The terms Contract, Summary, Task Outcome, Human Benefit Report, Knowledge,
Work Item, WIII, Agent, and Orchestrator retain their glossary meaning. A page
must distinguish repository evidence, adopter responsibility, and external or
provider responsibility.

## Capability coverage

The capability map must account for every adopter-facing ID in
`.ai/project/adopter-capability-manifest.json`:

| Manifest capability | User-facing treatment |
| --- | --- |
| `adopter_capability_manifest` | Explain that the installed capability surface is declared and validated; link to the advanced manifest reference. |
| `work_item_status_interface` | Link from the status/review route; explain that it is evidence-derived status, not an execution scheduler. |
| `governance_cost_metrics` | Mark as advisory evidence for governance cost; point to the technical reference. |
| `performance_diagnosis` | Mark as advisory timing/bottleneck diagnosis; do not promise optimization or a faster run. |
| `implementation_knowledge_query` | Link to the Knowledge user journey and exact-filter advanced reference. |
| `implementation_knowledge_projection` | Explain that records are derived from completed evidence and validated before use. |
| `implementation_knowledge_reports` | Link to Outcome and Human Benefit Report journeys. |
| `current_work_item_problem_resolution_boundary` | Link to lifecycle, stop/recovery, and Outcome guidance. |
| `template_capability_truth_material` | Clearly label as template material and evidence guidance, not an adopter guarantee by itself. |
| `implementation_approach_report` | Explain the implementation approach as evidence-bound reporting, not agent self-description. |

Rows with no localized reference retain an explicit advanced/English-fallback
label. `planned`, `template_only`, and externally owned behavior is never
worded as a current local guarantee.

## Required feature journeys

### Outcome, Summary, and Human Benefit Report

The page must answer the common question “what happened, what was fixed, what
remains, and what should I decide next?” It must separate:

- **Contract**: what the Work Item was allowed and expected to do;
- **Summary**: the change and verification handoff recorded during work;
- **Task Outcome**: evidence-backed lifecycle result, risks, stops,
  resolutions, and residual risks;
- **Human Benefit Report**: the concise human-facing projection and next safe
  action.

The example uses a problem → action → verification → result chain and shows
that an unsupported or unresolved claim remains a warning, red stop, unknown,
or human decision rather than becoming a success statement.

### Knowledge

The page must begin with a natural-language request such as “find the verified
Work Item that addressed the order service.” It then explains that the
interface searches validated archive-derived records through exact conjunctive
filters. It must state that the interface is read-only, deterministic, stable
in ordering, and not semantic search, vector search, or RAG. Missing, stale,
conflicting, or invalid evidence fails closed or remains visibly partial/
unknown according to the current implementation reference.

### Work Item parallel processing

The page must explain parallel Work Item processing, not parallel evaluation:

- separate independent Work Items use separate branches/worktrees and owned
  scopes;
- shared paths, shared generated projections, or shared evidence are
  serialized;
- bounded verification may run in parallel only where the configured check
  graph and evidence ownership permit it;
- WIII is a read-only current-worktree projection and is not a scheduler,
  retry controller, or agent manager;
- an external Agent or Orchestrator owns task dispatch, concurrency, retries,
  and provider coordination;
- AI Cockpit still validates each Work Item independently and prevents unsafe
  closure when evidence or ownership is incomplete.

The example pair must show one safe independent pair and one unsafe pair that
touches a shared path or projection and therefore must be serialized.

## Language parity

English, Simplified Chinese, and Japanese pages are semantic siblings, not
machine-translated copies. Each sibling preserves:

- the same reader goals and section order;
- the same natural-language examples and expected results;
- the same stop, recovery, human-decision, and evidence-boundary conditions;
- the same capability statuses and ownership labels;
- the same advanced command/path meaning.

Idiomatic wording is allowed. A technical reference without a translated
sibling must say so explicitly and link to the English canonical page. Link
labels, language switchers, and relative paths are checked in every language.

## Evidence and validation

Claims are checked against the Capability Truth Matrix, adopter capability
manifest, glossary, and the existing authoritative feature/reference pages.
The final review follows every root/docs/capability/feature link in all three
languages, checks the page contract, compares the semantic checklist, and runs
the repository documentation and governance checks declared by the Work Item
Contract. The final diff is inspected to ensure it contains only documentation
and generated documentation evidence. No release or version action is part of
the acceptance evidence.
