---
author: Ray
title: "Multilingual Documentation Understanding Journey Design"
description: Reader-first documentation governance for non-technical comprehension and bounded English, Japanese, and Simplified Chinese parity.
audience:
  - maintainer
  - contributor
status: historical
authority: implementation_record
lastVerifiedBy: documentation-understanding-journey-design
---

# Multilingual Documentation Understanding Journey Design

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Status and boundary

This document is an implementation design. It does not claim that the proposed
navigation, translations, registry, or checks already exist.

The implementation must be delivered as multiple governed Work Items. Each Work
Item owns one coherent change, one dedicated branch, and one pull request.

## Problem

AI Cockpit has substantial documentation, but the amount of documentation does
not make the project easy to understand. A first-time reader must infer the
project story from several directories, terminology appears before the reader
has a mental model, and Japanese or Simplified Chinese journeys can silently
return to English.

The current multilingual gates prove a bounded set of files and safety facts.
They do not prove that a non-technical reader can understand the project or
complete an important journey without changing language.

Documentation must remove project understanding as a bottleneck. If a
non-technical reader cannot explain the project's purpose, principles,
architecture, boundaries, human decisions, and first-use path, the core
documentation has not succeeded.

## Goals

1. Make North Star, philosophy, architecture, product boundaries, decision
   semantics, and adoption part of one visible core narrative.
2. Give English, Japanese, and Simplified Chinese readers complete journeys for
   important topics without requiring every repository document to be
   translated.
3. Write the first explanatory layer for a non-technical reader and expose
   engineering detail through progressive disclosure.
4. Make importance, localization requirements, ownership, navigation, and
   verification machine-readable.
5. Prevent future changes from reintroducing hidden paths, silent English
   fallback, competing canonical pages, or safety-semantic drift.

## Non-goals

- Translate every reference, audit, release, plan, design, or historical file.
- Replace technical reference material with simplified prose.
- Claim that readability scores prove human understanding.
- Maintain separate, competing "simple truth" and "technical truth" pages.
- Change runtime, Work Item lifecycle, security, or release behavior as part of
  documentation restructuring.
- Treat machine translation alone as semantic or native-language review.

## Chosen approach

Use a reader-journey model backed by criticality tiers and executable
multilingual governance.

This approach is preferred over link-only repair because link repair does not
fix the missing project narrative. It is preferred over translating the whole
repository because low-frequency evidence and historical material would create
large maintenance cost without improving the main reader journey.

## Core narrative

The primary understanding journey is:

```text
North Star
  → Problem and purpose
  → Design philosophy
  → Product architecture
  → Capabilities and boundaries
  → Human decisions and status
  → Adoption and first use
  → Recovery and deeper reference
```

Installation is an action after understanding, not the first explanation of the
product.

Every localized documentation home must expose this sequence directly. A reader
may enter at a later step, but each core page must show where it sits in the
sequence and offer a same-language next step.

## Reader journeys

### Understand the project

The reader can explain:

- what AI Cockpit is trying to achieve;
- which failure in AI-assisted development it addresses;
- why evidence, bounded authority, fail-closed behavior, and human control are
  design principles;
- how Intent, Contract, Implementation, Verification, Summary, Cockpit, and
  Human Decision relate;
- what AI Cockpit does not provide.

### Evaluate adoption

The reader can decide whether the project fits their team, identify external
responsibilities, estimate the governance cost, and choose an adoption path.

### Begin using it

The reader can install from a fixed release, calibrate a repository, start the
first Work Item, recognize stop conditions, and find recovery guidance.

### Review an outcome

The reader can interpret Green, Yellow, Red, evidence, unknowns, residual risk,
and the human decision requested by the system.

### Operate and recover

The reader can identify the current lifecycle stage, understand why execution
stopped, avoid unsafe improvisation, and follow the correct recovery owner and
route.

### Maintain the system

Technical readers can move from the same core narrative into schemas, commands,
policies, scripts, tests, security controls, and audit evidence without changing
the meaning of the core explanation.

## Documentation criticality model

### P0: core understanding and safe adoption

P0 topics must have complete English, Japanese, and Simplified Chinese pages.
Their localized links must form complete same-language journeys.

Initial P0 topics:

1. Documentation home and project overview
2. North Star
3. Problem and purpose
4. Design philosophy
5. Product architecture and evidence flow
6. Capabilities, non-capabilities, and external boundaries
7. Decision states and human control
8. Adoption overview and 30-second orientation
9. Installation and first calibration
10. First Work Item
11. How to read Cockpit Status and Task Outcome
12. Work Item lifecycle and stop conditions
13. Recovery overview
14. Security and trust boundary overview

The implementation may assign closely related P0 topic identifiers to one
canonical page when doing so improves the journey. Every topic identifier and
its next-topic relationship remains explicit in the registry. A topic must not
be removed from P0 merely to reduce the translation count.

### P1: common operation and maintainer depth

P1 topics require a localized summary and route from each supported language.
Full technical detail may remain in one canonical language when translation cost
is not justified. Any fallback must be explicit, for example:

> Detailed technical reference — English

Typical P1 content includes command reference, schema reference, individual
security mechanisms, advanced lifecycle recovery, calibration internals, and
maintainer procedures.

### P2: evidence, history, and specialist material

P2 has no default translation requirement. It includes audit records, release
notes, archived Work Items, historical plans, implementation designs, test
architecture evidence, and narrow specialist references.

P2 documents must still have correct authority and historical metadata. A P2
page must not become the only source of a fact required to understand a P0
journey.

## Canonical semantic ownership

Each topic has one canonical semantic owner. Localized siblings express the
same bounded meaning; they do not create independent product truth.

The canonical owner contains both layers needed by its audience:

1. a plain-language explanation and concrete scenario;
2. links or sections for technical details and evidence.

Compatibility pages redirect to the canonical owner. Documentation homes and
journey maps provide navigation but do not duplicate the full explanation.

When a technical fact changes, the owning topic and every required P0 locale
must change in the same Work Item unless the Contract explicitly proves that
the change has no multilingual semantic impact.

## Proposed documentation registry

Extend `docs/reference/documentation-authority-registry.json` to schema version
2. Version 2 retains the current agent-instruction authority entries and adds
reader topic, criticality, localization, journey, and semantic-invariant data.
The checker must continue to read schema version 1 during migration, but new
repository state is written only as version 2. Do not create a second topic
registry.

Each current-facing topic needs fields equivalent to:

```json
{
  "topic": "product-architecture",
  "criticality": "P0",
  "canonicalPath": "docs/architecture.md",
  "localizedPaths": {
    "en": "docs/architecture.md",
    "ja": "docs/architecture.ja.md",
    "zh-CN": "docs/architecture.zh-CN.md"
  },
  "audiences": ["adopter", "maintainer"],
  "journeys": ["understand", "maintain"],
  "nextTopics": ["product-boundaries", "decision-states"],
  "enforcementStatus": "planned",
  "plainLanguageRequired": true,
  "semanticInvariants": [
    "ai-cockpit-is-repository-governance",
    "external-controls-remain-external"
  ]
}
```

The registry is the policy source for coverage and navigation checks. It is not
a content generator and must not become a second prose authority.

During migration, `enforcementStatus` is either `planned` or `active`.
`planned` records the complete intended P0 inventory and emits visible gaps but
does not claim coverage or block unrelated repository work. `active` enables
all locale, navigation, and parity gates for that topic. A topic can move to
`active` only in the Work Item that supplies and verifies every required P0
locale. The initiative cannot complete while any P0 topic remains `planned`.
Changing an `active` topic back to `planned` is forbidden because it would
weaken an established gate.

## Localized documentation homes

Add one documentation home per supported language at these paths:

- `docs/README.md`
- `docs/README.ja.md`
- `docs/README.zh-CN.md`

The localized root README links to its matching documentation home. Each home
uses reader goals, not repository directories, as the primary navigation:

- Understand AI Cockpit
- Decide whether to adopt it
- Start using it
- Review a result
- Recover from a stop
- Maintain or audit it

Directory-based reference navigation remains available below the journeys for
technical readers.

## P0 writing contract

Every P0 page must begin with a non-technical explanatory layer in this order:

1. **Purpose:** one sentence stating the reader's question.
2. **Audience:** who should read the page.
3. **Outcome:** what the reader will understand or decide.
4. **Scenario:** a concrete example before abstract terminology.
5. **Explanation:** plain-language concepts and the minimum useful diagram.
6. **Action or decision:** what the reader can do with the understanding.
7. **Stop conditions:** when not to continue or guess.
8. **Next step:** one to three same-language links.
9. **Technical depth:** commands, fields, policies, and evidence after the core
   explanation.

Formal terminology may be retained, but its first use must include a plain
explanation. For example:

> Before editing, AI Cockpit checks whether the task has enough evidence to
> proceed safely. If essential information is missing, it stops instead of
> guessing. This is the Preflight Review's fail-closed behavior.

Writers must prefer short sentences, explicit actors, concrete outcomes, and
examples. Unexplained acronyms, internal filenames, and command sequences must
not carry the first explanation of a concept.

## Progressive disclosure

Progressive disclosure is a content rule, not a separate truth hierarchy.

```text
Plain explanation
  → Scenario and visual model
  → User decision or action
  → Technical mechanism
  → Evidence and specialist reference
```

Non-technical readers can stop after the decision layer without receiving a
misleading simplification. Technical readers continue into the same topic's
mechanism and evidence.

## Navigation rules

1. Every P0 topic is reachable from the matching localized root README in no
   more than two links.
2. A P0 page links to the same locale for every P0 next step.
3. A language switch keeps the reader on the same topic.
4. Silent fallback to English is forbidden on P0 routes.
5. P1 English-only depth is allowed only through a visibly labelled fallback.
6. Each P0 page has one to three next steps; large unranked link lists are not
   sufficient navigation.
7. A compatibility page is not counted as an extra reader step when it performs
   a direct, clearly labelled redirect, but navigation should link directly to
   canonical pages wherever possible.
8. Historical and archived documents must not appear as current journey steps.

## Automated governance

### Registry validation

Fail when:

- a current topic has duplicate canonical owners;
- a P0 topic lacks any required locale;
- a registered path is missing or has incompatible authority metadata;
- a P2 page is the only owner of a P0 semantic invariant;
- a journey references an unknown topic.
- an active topic is downgraded to planned.

Planned-topic gaps are emitted as an inventory report and are never described
as passing multilingual coverage.

### Localized link graph validation

Build a link graph from registered pages and fail when:

- a P0 topic is more than two links from its localized entry;
- a P0 next step changes language;
- a P0 page is stranded or missing its declared next topic;
- a language switch does not resolve to the same topic;
- a P1 English fallback lacks an explicit language label;
- a current journey enters `docs/archive/` or other historical evidence.

### Structural parity validation

P0 localized siblings must preserve the same topic identity, purpose, safety
boundaries, stop conditions, capability limitations, and declared next topics.
Heading text and paragraph count need not be byte-for-byte equivalent.

Use stable semantic identifiers for safety-critical statements. Do not use raw
heading equality or machine translation similarity as the only proof of parity.

### Plain-language validation

Automated checks may detect missing P0 sections, undefined acronyms, excessive
first-paragraph complexity, and commands appearing before the explanatory
layer. These are review signals unless a deterministic structural rule is
violated.

Readability scores must not be treated as evidence of comprehension.

### Existing gate integration

Extend the current documentation metadata and multilingual checks where their
responsibility already matches the new rule. Add a separate focused checker
only when link-graph or registry validation would make the existing checker
unclear or overly coupled.

All new check behavior requires focused unit tests with positive and negative
fixtures. The Make entrypoint must remain the public verification route.

## Human comprehension validation

P0 readiness requires scenario-based review by a reader who is not relying on
repository implementation knowledge. Native-language review is required before
claiming Japanese or Simplified Chinese editorial quality.

After the core journey, the reviewer should be able to answer:

1. What problem does AI Cockpit solve?
2. What is its North Star?
3. How does a human intention become reviewable evidence?
4. What does AI Cockpit explicitly not control?
5. When will it stop, and why is stopping useful?
6. What is the next safe step to try it?

A review passes when the reader answers at least five questions correctly and
has no critical misconception about authority, security, verification, or human
control. Findings are recorded as evidence; they are not replaced by a prose
claim that the documentation is easy to understand.

## Failure and recovery behavior

- Missing P0 locale: block the documentation change or release gate that claims
  multilingual completeness; add the locale in the same Work Item.
- Safety-semantic mismatch: block; correct the localized content and obtain the
  required language review.
- Broken or wrong-language P0 route: block; repair the route or the registry.
- Missing P1 translation: do not block when the localized summary and explicit
  English fallback satisfy policy.
- Missing P2 translation: no failure.
- Failed comprehension review: keep the affected P0 topic draft or not ready;
  revise the explanation before promoting the journey.
- Unavailable native-language reviewer: report editorial quality as unverified;
  do not infer it from file presence or automated translation.

## Implementation Work Items

### WI-1: criticality registry and executable policy

- Inventory current-facing documentation by topic, owner, audience, journey,
  criticality, and locale.
- Extend the existing documentation authority model or define its compatible
  successor.
- Implement registry, coverage, and localized link-graph checks with tests.
- Do not change product claims or translate content in this Work Item.

### WI-2: localized homes and entry navigation

- Add English, Japanese, and Simplified Chinese documentation homes.
- Update localized root READMEs to use the core narrative and reader journeys.
- Keep P0 destinations visible within two links.
- Remove silent language fallback from the entry layer.

### WI-3: North Star, philosophy, architecture, and boundaries

- Establish or repair one canonical owner for each topic.
- Create complete English, Japanese, and Simplified Chinese P0 siblings.
- Apply the P0 writing contract and progressive disclosure.
- Preserve technical depth and evidence routes without leading with them.

### WI-4: decisions, lifecycle, status, and recovery

- Localize and rewrite Decision States, Work Item lifecycle, status
  interpretation, stop conditions, and recovery as one continuous journey.
- Ensure every status explains the human decision and next safe action.
- Keep advanced recovery mechanics in P1 where appropriate.

### WI-5: adoption and security journey closure

- Reconcile existing trilingual installation and calibration content with the
  new homes and narrative.
- Add the P0 security and trust-boundary overview in all three languages.
- Keep individual mechanisms and supply-chain detail in P1 when appropriate.
- Remove duplicated or obsolete current-facing routes only through documented
  compatibility handling.

### WI-6: human validation and governance stabilization

- Run the comprehension protocol in English, Japanese, and Simplified Chinese.
- Correct misunderstandings and record bounded review evidence.
- Verify all automated documentation gates and full repository checks.
- Update capability and multilingual claims only to the level proven by the
  final evidence.

Each Work Item must update the active Contract when discovered file ownership
extends beyond its declared scope. Work Items must not be combined merely to
reduce pull-request count.

## Verification strategy

Focused verification for implementation Work Items must include:

- registry schema and ownership tests;
- missing-locale and invalid-criticality fixtures;
- same-language, depth, stranded-page, and fallback-label link fixtures;
- semantic-invariant parity fixtures;
- P0 structural contract fixtures;
- existing documentation metadata and multilingual tests;
- repository link validation;
- generated documentation status consistency where applicable;
- the complete AI Cockpit Finish criteria declared by each Contract.

Translation Work Items additionally require review evidence for technical
meaning, safety boundaries, and natural-language quality. A green automated
check without the declared human review must not be reported as complete
editorial validation.

## Success measures

The governance should optimize for:

- completion of the six comprehension questions;
- zero critical misconceptions in reviewed P0 journeys;
- zero silent English fallbacks in P0 Japanese and Simplified Chinese paths;
- every P0 topic reachable within two links from its localized root README;
- one canonical semantic owner per topic;
- explicit P1 fallback labels;
- no P2 translation work created solely to improve a raw coverage percentage.

Raw translated-file count is an inventory metric, not the success criterion.

## Acceptance for the complete initiative

The initiative is complete only when:

1. all registered P0 topics have English, Japanese, and Simplified Chinese
   content;
2. the core narrative is visible and ordered consistently in all three
   documentation homes;
3. a non-technical reader can understand North Star, philosophy, architecture,
   boundaries, decisions, and first use before reading specialist reference;
4. localized P0 routes pass the graph, parity, metadata, and structural checks;
5. human comprehension evidence meets the stated threshold in all three
   languages without critical misconceptions;
6. P1 and P2 behavior follows the bounded translation policy;
7. current capability claims describe only the evidence actually obtained.

## Rollback

Registry and gate Work Items must remain compatible with the previous
documentation authority data until all P0 topics are migrated. If a journey
cannot be completed safely, keep the old canonical route available, mark the
new route draft, and correct it in the same active Work Item or a governed
successor. Never solve migration failure by weakening multilingual or safety
checks.
