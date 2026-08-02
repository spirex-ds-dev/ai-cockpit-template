---
author: Ray
title: Canonical terminology
description: Machine terms, semantic domains, and localized human labels.
---

# Canonical terminology

AI Cockpit uses canonical English machine values in contracts, receipts, and
automation. Human-facing reports may use the matching localized label, but
must preserve the canonical value where it is evidence.

## Semantic domains

| Domain | Canonical values | Meaning |
| --- | --- | --- |
| Governance Profile | `light`, `standard`, `strict` | Governance and verification intensity selected for a Work Item. |
| Calibration Profile | `lite`, `standard`, `strict` | Proportional project-control policy. This is a separate compatibility domain. |
| Human status color | `green`, `yellow`, `red`, `unknown` | A concise, human-readable Outcome signal. |

`light` and `lite` are deliberately not aliases. A Governance Profile must use
`light`; a Calibration Profile must use `lite`. `standard` and `strict` occur
in both domains, but retain the meaning of the field that contains them.

`release` is not a Governance Profile. Release work uses `strict` plus the
explicit release operation and its required verification escalations.

## Human status mapping

| Canonical value | English | 日本語 | 简体中文 | Interpretation |
| --- | --- | --- | --- | --- |
| `green` | green | 緑 | 绿色 | Complete and supported by the required evidence. |
| `yellow` | yellow | 黄 | 黄色 | Delivered with a bounded warning, residual risk, or required attention. |
| `red` | red | 赤 | 红色 | Blocked, failed, or requires intervention before continuing. |
| `unknown` | unknown | 不明 | 未知 | Evidence is insufficient; do not infer a favorable state. |

These colors improve scanning for a human reader; they do not replace the
underlying Outcome evidence, verification records, or decision requirements.
