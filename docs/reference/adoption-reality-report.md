---
author: Ray
title: "Adoption Reality Report"
description: "Evidence boundary between template capability truth and adopter/provider state."
audience:
  - adopter
  - auditor
status: reference
authority: canonical
lastVerifiedBy: tests/test_ai_adoption_reality_report.py
keywords:
  - adoption
  - capability-truth
  - external-evidence
---

# Adoption Reality Report

The report is a conservative view of what this template provides and what an
adopter has actually verified. It does not turn files in the template checkout
into proof that a target repository or hosted provider is configured.

Generate a repository-local report with:

```text
PYTHONPATH=scripts:. python scripts/ai_adoption_reality_report.py
```

The command writes a machine-readable JSON report and a human-readable
Markdown report under `target/`. It is deterministic for the same inputs and
keeps the existing `Outcome` and `task_report` JSON/Markdown pair as the
governed Work Item delivery projections. This report is not a second source of
Outcome truth.

## Status vocabulary

| State | Meaning | What it does not mean |
| --- | --- | --- |
| `implemented`, `template_only`, `adopter_installed`, `planned` | Template Capability Truth Matrix status. | It does not prove the adopter executed the capability. |
| `verified` | An adopter control has an explicit, non-template-owned evidence reference. | It does not authenticate the evidence producer or prove provider enforcement. |
| `not_configured` | No adopter evidence was supplied. | It is not a pass or readiness signal. |
| `unknown` | Available evidence is insufficient or ambiguous. | The report must not infer success. |
| `external_responsibility` | The adopter/provider-owned system must supply the evidence. | Repository-local checks cannot replace that evidence. |

The ten adopter controls are installation, calibration, hosted CI, branch
protection, external identity, CodeQL, SBOM, provenance, signing, and
production sandbox. Hosted CI, branch protection, external identity, and
production sandbox require provider or adopter-system evidence; the report
does not inspect those systems. CodeQL, SBOM, provenance, and signing also
remain adopter-owned verification concerns even when the template contains
related documentation or release artifacts.

Template-owned files such as `.ai/cockpit/sbom.json` and
`.ai/cockpit/provenance.json` cannot satisfy an adopter `verified` state. A
missing, malformed, unsupported, or expired evidence record remains
`not_configured` or `unknown`, and readiness remains `not_claimed`.

## Outcome delivery boundary

The report is supplemental reference evidence. Work Item `Outcome` remains
machine-readable, and `task_report.md` remains human-readable, generated from
the existing governed projection path. A report or Markdown rendering must not
claim completion, provider identity, branch protection, enterprise
compliance, production sandboxing, or security control effectiveness without
the corresponding external evidence.
