---
title: Real Adopter Reference Validation
author: Ray
description: Bounded disposable-clone evidence for three public reference projects.
---

# Real Adopter Reference Validation

Run the bounded reference validator against disposable clones of its public
catalog:

```sh
PYTHONPATH=scripts .venv/bin/python scripts/real_adopter_reference_validation.py \
  --output target/real-adopter-reference-validation
```

Each Evidence Pack records the source URL, immutable revision, lifecycle phase
result, and before/after path classification for one reference project. The
runner replaces the clone's public `origin` with a local bare repository before
any installer action, and never pushes, opens a pull request, or changes source
repository configuration.

The evidence proves only disposable local-clone behavior. It does not prove
provider identity, hosted CI, branch protection, review, audit, permissions, or
release status. A missing native toolchain is recorded as `not_run` with a
recovery condition, never as a pass.
