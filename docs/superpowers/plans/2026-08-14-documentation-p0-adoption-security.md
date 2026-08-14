---
author: Ray
title: "Documentation P0 Adoption and Security Journey Plan"
description: "Implementation record for the WI-5 trilingual adoption and security route."
status: historical
authority: implementation_record
---

# Documentation P0 Adoption and Security Journey Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

## Goal

Close the reader's first-use path in English, Japanese, and Simplified Chinese:
installation → calibration → first Work Item, with a clear security boundary.

## Tasks

1. Reconcile the three localized documentation homes and installation links.
2. Add same-language first-calibration and first-work-item pages.
3. Add a P0 injection/trust-boundary overview in all three languages.
4. Activate registry topics only after structural route and semantic tests pass.

## Verification

- Run `pytest -q tests/test_documentation_p0_adoption_security.py`.
- Run the repository AI checks and strict quality finish flow.
- Confirm every localized route has a same-language next link and names external
  security responsibility without claiming sandbox or provider authority.
