---
author: Ray
title: "Standard Adoption Guide"
description: "Evidence-backed installation, calibration, Work Item, and review guidance for adopters."
keywords:
  - adoption
  - governance
  - verification
---

# Standard Adoption Guide

Commands in this guide are repository-local guidance. Mark each command according to the evidence actually available:

| Evidence label | Meaning |
| --- | --- |
| `syntax_tested` | The command syntax was checked; execution is not claimed. |
| `fixture_executed` | A controlled fixture executed it; adopter behavior is not claimed. |
| `hosted_executed` | Hosted CI executed the declared fixture/gate. |
| `adopter_required` | The adopter must execute and review the result. |
| `illustrative_only` | Example shape only; do not copy without calibration. |

Installation creates reviewable repository evidence. It does not prove provider identity, approval, production readiness, or enterprise compliance. Use the current version and capability matrix as the source of truth, and treat older plans and archived documents as historical context.
