---
author: Ray
title: "Schemas"
description: "Reference map for AI Cockpit governance record schemas and validators."
audience:
  - contributor
  - maintainer
  - auditor
status: reference
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Schemas

| Record | Authority |
| --- | --- |
| Work Item Contract and AI Change Summary | [Contract Fields](../contract-fields.md) and repository schema validators |
| Project Profile | `.ai/project_profile.yaml` plus `scripts/ai_project_profile.py` |
| Cockpit checks | `.ai/cockpit/checks.yaml` |
| Capability status | [capability-truth-matrix.json](capability-truth-matrix.json) |
| Documentation context | [documentation-context-registry.json](documentation-context-registry.json) |
| Archive discovery | `.ai/work-items/archive/index.json` and immutable archive manifests; each new manifest also records the content-addressed pre-archive candidate-coverage report digest and binding |
| Work Item Intelligence Snapshot | `.ai/schemas/work-item-intelligence-snapshot.schema.json` and `scripts/ai_work_item_intelligence.py` |
| External handoff | `.ai/schemas/external_handoff.schema.json` and `scripts/ai_external_handoff.py`; receipt bindings must exactly match the handoff |

Examples are explanatory. The executable validators and versioned
machine-readable records decide whether a concrete instance is valid.
