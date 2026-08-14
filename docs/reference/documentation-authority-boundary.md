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

Schema version 2 adds a reader-topic inventory. `criticality` describes how
central a topic is to understanding the project: P0 is a core explanation, P1
is an important supporting route, and P2 is specialist reference. A topic's
`enforcementStatus` is `planned` while migration is being prepared and `active`
only when its declared routes are present. Planned gaps are reported visibly
but do not pretend that a translation is complete; an active P0 topic must
provide English, Japanese, and Simplified Chinese routes.

Authority answers “which document may guide an agent?” The reader-topic policy
answers “which path should a person follow to understand and use the project?”
They are checked together, but the default agent read set remains authority-only.
