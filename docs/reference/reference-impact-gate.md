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

The Reference Impact Gate evaluates observable operation impact, not a requester's presumed intent. It covers removal, rename, move, deprecation, visibility or signature change, configuration or public API change, and Maven module removal. It produces `continue`, `needs_human_confirmation`, or `block`; it never treats a search with no matches as proof that dynamic or external references are absent.

## Use

Create a version 1 record under `.ai/evidence/reference-impact/` and run:

```sh
make check-ai-reference-impact
```

`check-ai-pr` runs the same target. Decisions are written to `target/reference-impact/`. A `block` or `needs_human_confirmation` decision exits non-zero in enforced mode. When the active Work Item has an impact-bearing changed path but no covering record, the gate stops with `needs_human_confirmation` and a recovery condition; it is never an empty successful check. Ordinary documentation and other no-impact paths use the `not_applicable` fast path.

The operation-impact report keeps request trust, authority binding, safety evidence, and scope consistency as separate facts. The effective decision is the strictest one. A request saying that something is unused, approved, or safe is a claim to test against repository evidence, not proof. An unresolved factual conflict cannot be cleared by another verbal confirmation.

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

- `block`: a repository-local static, test, documentation, configuration, workflow, or Maven build reference remains, or a declared operation conflicts with actual changed-path facts. Remove or migrate the live reference and correct the declared scope before rerunning.
- `needs_human_confirmation`: impact evidence is incomplete, requested wording asks to bypass analysis, or claimed approval is not independently bound to the target. The gate stops and states the evidence or authorization needed to resume; it does not infer malicious intent or permanently reject the change.
- `needs_human_confirmation`: dynamic, external, or monitoring evidence is unknown, empty, or stale; governance evidence is incomplete; or the operation removes a public API or configuration key. Supply current migration and owner evidence, then rerun.
- `continue`: all repository-local categories are clear and all non-local and governance evidence is explicit.

Unsupported languages use `generic_analysis_only`. Python uses AST name analysis; TypeScript uses basic text analysis. Generic analysis can miss reflection, generated code, aliases, runtime loading, external repositories, and monitoring consumers. It can also report textual matches that are not executable references. These limitations are reasons to preserve explicit unknown states, not to claim complete semantic analysis.

For a Maven `build_module`, the local analysis searches parent `<modules>` declarations, POM artifact/dependency text, and test references to the module path or POM. This is a conservative local signal, not proof of all runtime, published, or external consumers.

Legacy records are readable only when they already conform to version 1. The checker does not rewrite old or archived evidence and does not infer missing fields. Paths must be repository-relative; path traversal and symbolic-link targets are rejected.
