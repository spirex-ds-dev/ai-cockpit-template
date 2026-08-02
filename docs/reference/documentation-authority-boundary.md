---
author: Ray
title: "Documentation Authority Boundary"
description: Machine-readable routing policy for current, reference, and historical documentation.
authority: reference
instructional: false
status: current
supersededBy:
---

# Documentation Authority Boundary

The [authority registry](documentation-authority-registry.json) separates
documentation routing from document prose. It uses `canonical`, `reference`,
and `historical` authority values, plus `instructional`, `status`, and
`supersededBy` fields.

- `docs/current/` contains current canonical instructional documents and is the
  default agent read set.
- `docs/reference/` is current supporting material and is returned only by an
  explicit reference opt-in.
- `docs/archive/` records historical material. It is never returned as current
  instruction, even when an agent requests reference material.

The registry enforces one canonical document per declared topic. Existing
documentation metadata and historical records remain in place as compatibility
evidence; this boundary does not rewrite archived Work Items or infer authority
from prose. Querying `scripts/ai_documentation_authority.py` is read-only.
