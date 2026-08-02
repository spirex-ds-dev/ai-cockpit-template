---
author: Ray
title: "Multilingual Semantic Parity"
description: "Fail-closed comparison for controlled governance semantics across English, Japanese, and Chinese."
keywords:
  - ai-cockpit
  - multilingual
  - semantic-parity
  - governance
---

# Multilingual Semantic Parity

Localized governance views may translate presentation chrome, but they must not
change controlled facts. `scripts/ai_multilingual_semantic_parity.py` compares
English, Japanese, and Simplified Chinese projections for status, prohibited
claims, safety boundaries, human decisions, risks, limitations, commands,
paths, and capability claims.

The comparison is deliberately narrow: arbitrary evidence prose remains source
text and is not treated as a machine-translated semantic claim. A missing
restriction, an extra capability claim, or a different command or path fails
closed rather than being hidden by matching section headings.
