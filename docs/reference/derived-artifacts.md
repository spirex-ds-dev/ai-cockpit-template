---
author: Ray
title: "Derived Artifact Authority"
description: "The executable fact-to-view boundary for AI Cockpit governance outputs."
keywords:
  - ai-cockpit
  - evidence
  - derived-artifacts
  - authority
---

# Derived Artifact Authority

AI Cockpit separates authoritative governance facts from files rendered for review.
Contracts, Summaries, event logs, and archived Task Outcome JSON are facts. Status,
Task Outcome Markdown, and Human Benefit Reports are derived views. A view must never
be read back as a fact for a later decision.

`.ai/cockpit/derived_artifacts.json` is the executable registry for that boundary. Each
view declares its generator, its fact inputs, any earlier view it renders, and the
single source authority for every declared output field. The registry rejects a view
declared as a fact, a missing authority, and dependency cycles.

Validate the registry and print its stable content digest with:

```sh
python scripts/ai_derived_artifacts.py .ai/cockpit/derived_artifacts.json
```

The registry does not rewrite historical archives or replace the required human-facing
Outcome. It documents and verifies the authority boundary for active generators, so a
regenerated Status or report remains a view of the same recorded evidence.
