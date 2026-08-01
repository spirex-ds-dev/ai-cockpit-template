---
author: Ray
title: "Reference Impact Gate"
description: Evidence-backed decisions before destructive or compatibility-affecting repository changes.
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - reference_impact_gate
keywords:
  - ai-cockpit
  - reference-impact
  - destructive-change
---
# Reference Impact Gate

The Reference Impact Gate evaluates a declared removal, rename, move, deprecation, visibility or signature change, configuration removal, or public API removal before the change is accepted. It produces `continue`, `needs_human_confirmation`, or `block`; it never treats a search with no matches as proof that dynamic or external references are absent.

## Use

Create a version 1 record under `.ai/evidence/reference-impact/` and run:

```sh
make check-ai-reference-impact
```

`check-ai-pr` runs the same target. Decisions are written to `target/reference-impact/`. A `block` or `needs_human_confirmation` decision exits non-zero in enforced mode.

The canonical schema is `.ai/schemas/reference_impact.schema.json`. A minimal automatically eligible record must include repository-local analysis inputs, non-empty evidence for dynamic references, external consumers, and monitoring, plus evidence that the Contract, acceptance criteria, and destructive-change policy declare the operation.

```json
{
  "version": 1,
  "target": {
    "type": "function",
    "name": "calculate_total",
    "path": "src/order.py",
    "operation": "delete"
  },
  "referenceAnalysis": {
    "dynamicReferences": {"status": "proven_absent", "evidence": ["report:dynamic"]},
    "externalConsumers": {"status": "proven_absent", "evidence": ["owner:migration"]},
    "monitoringReferences": {"status": "proven_absent", "evidence": ["dashboard:query"]}
  },
  "governanceEvidence": {
    "contractDeclared": true,
    "acceptanceDeclared": true,
    "destructiveChangeAllowed": true,
    "evidence": ["contract", "acceptance", "policy"]
  }
}
```

## Decisions and recovery

- `block`: a repository-local static, test, documentation, configuration, or workflow reference remains; bypass wording is present; or weak identity evidence is presented as destructive authority. Remove or migrate the live reference, or replace the invalid request.
- `needs_human_confirmation`: dynamic, external, or monitoring evidence is unknown, empty, or stale; governance evidence is incomplete; or the operation removes a public API or configuration key. Supply current migration and owner evidence, then rerun.
- `continue`: all repository-local categories are clear and all non-local and governance evidence is explicit.

Unsupported languages use `generic_analysis_only`. Python uses AST name analysis; TypeScript uses basic text analysis. Generic analysis can miss reflection, generated code, aliases, runtime loading, external repositories, and monitoring consumers. It can also report textual matches that are not executable references. These limitations are reasons to preserve explicit unknown states, not to claim complete semantic analysis.

Legacy records are readable only when they already conform to version 1. The checker does not rewrite old or archived evidence and does not infer missing fields. Paths must be repository-relative; path traversal and symbolic-link targets are rejected.
