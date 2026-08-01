---
author: Ray
title: "Input Trust Dataflow"
description: "Bounded provenance and trust labels for indirect-injection handling."
---

# Input Trust Dataflow

This repository preserves a local provenance record when content moves between
steps. The record classifies content; it does not authenticate an identity,
verify a provider event, or authorize an external operation.

## Sources and trust labels

| Source | Initial trust label |
| --- | --- |
| `direct_user_instruction` | `authority` |
| `repository_policy` | `authority` |
| `repository_document` | `repository_content` |
| `issue_content`, `pull_request_comment`, `external_web_content`, `build_log`, `test_fixture` | `untrusted_content` |
| `generated_agent_content` | `generated_content` |
| `tool_output` | `unknown_source` |
| `provider_verified_event` | `provider_verified` |

Labels are provenance facts, not permission. A local transformation cannot
relabel its source into a different trust class. Markdown commands remain
content, Issue role claims are not identity evidence, and generated conclusions
cannot become independent evidence in a later step.

## Tool output and propagation

Tool output is `raw_data`, `tool_interpretation`, or `agent_interpretation`.
Interpretations are generated content and retain the original provenance chain.
Cross-step propagation appends `cross_step` while preserving source and label.

For a high-risk operation, a missing chain, untrusted or unknown content, or a
generated conclusion produces a local `block` with a safe alternative and
recovery condition. A provider-derived label still does not bypass separate
operation-time authority and evidence gates.

## Limits

The model is deterministic repository-local policy. It does not authenticate
users, verify provider events, or execute the operation named in content.
