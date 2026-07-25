---
author: Ray
title: "Test Architecture"
description: "Executable test-layer and local quality-check boundaries for AI Cockpit."
keywords:
  - ai-cockpit
  - testing
  - quality
  - governance
---

# Test Architecture

This repository uses layered, negative-first verification. A layer is only
reported as `verified` when the checkout contains explicit evidence for it;
otherwise it is recorded as `not_applicable`, never silently treated as pass.

The local executable boundary is `scripts/ai_quality_architecture.py`. It
reports the test-layer evidence and fails closed on observable `shell=True`,
path-traversal literals, parse/encoding errors, and mutable function defaults.
The checker is intentionally narrow: it cannot establish provider, adopter,
identity, production, legal, or complete prompt-injection controls.

Required layers are:

| Layer | Evidence expectation |
| --- | --- |
| Unit / schema / state machine / property | deterministic focused tests |
| Transaction / installer integration / adopter fixture | rollback and fixture tests |
| Hosted smoke / security / prompt injection / absurd | explicit negative or boundary tests |
| Release / documentation | release and documentation regression tests |

Run the local report with:

```sh
make check-quality-architecture
```

The JSON report under `target/` is generated evidence and must not be edited
by hand. A missing layer is a review signal; it does not prove the capability
is absent from all environments.
