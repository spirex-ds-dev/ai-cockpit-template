---
author: Ray
title: "Documentation Architecture"
description: Documentation information architecture for AI Cockpit.
audience:
  - maintainer
  - contributor
status: reference
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords:
  - ai-cockpit
  - documentation
  - information-architecture
  - quick-start
  - reference
---

# Documentation Architecture

## Canonical layers

```text
docs/
├── getting-started/  installation, first calibration, first Work Item
├── concepts/         trust, evidence governance, decision states
├── operations/       quality gates, lifecycle, recovery
├── security/         threat, injection, and supply-chain boundaries
├── reference/        capability truth, schemas, commands
└── archive/          historical plan, review, and design entrypoints
```

Current formal pages declare `audience`, `status`, `authority`, and
`lastVerifiedBy`. Allowed audiences are `adopter`, `maintainer`,
`security_reviewer`, `auditor`, and `contributor`; allowed statuses are
`current`, `reference`, `historical`, and `draft`; allowed authorities are
`canonical`, `derived`, `explanatory`, and `archived_evidence`.

One topic has one canonical owner. Compatibility pages link to that owner;
historical entrypoints preserve context but never become runtime instruction.

This page is for documentation maintainers. It defines authoritative ownership,
language mapping, and current-versus-historical context; adopters normally enter
through their language README and installation guide.

主要入口は各言語内で完結します。英語は [Installation](../getting-started/installation.md)、中文は[完整中文安装手顺](../getting-started/installation.zh-CN.md)、日本語は[日本語インストール手順](../getting-started/installation.ja.md)です。英語版だけを完全版として扱わず、3 言語の章順序・安全境界・platform 例を一致させます。

## Authoritative entry points

| Need | Authoritative page |
| --- | --- |
| Runtime/component facts | [Architecture](../architecture.md) |
| Contract and Summary field semantics | [Contract Fields](../contract-fields.md) |
| Reviewer interpretation of generated state | [How to Read Cockpit Status](how-to-read-cockpit-status.md) |
| Agent execution and lifecycle rules | [Cockpit runtime guide](../../.ai/cockpit/README.md) |

The README files are short five-minute positioning and entry points. They do not carry the complete feature catalogue or Release Reference. The authoritative pages below assign detailed philosophy, architecture, field semantics, status interpretation, and execution rules to their respective layers.

This page describes the stable documentation split for AI Cockpit. It keeps the guided adoption flow short, moves support material into reference pages, and gives the README a clear entry path for first-time readers.

## Page Roles

| Page | Role | Reader question |
| --- | --- | --- |
| [README.md](../../README.md) | Entry page | What is this, and how do I start quickly? |
| [Trilingual Installation](../getting-started/installation.md) | Beginner adoption source route | Where do I start, what short prompt do I copy, what result should I see, and when do I stop? |
| [Strict Installation and Supply-Chain Verification](../getting-started/installation-security.md) | Security-owner route | How are release metadata, assets, SHA-256, mirrors, and exceptions verified? |
| [Project Calibration Guide](../getting-started/calibration.md) | Project-calibrator route | Which plain-language project questions must a calibration Work Item answer? |
| [Calibration Session Model](calibration-session-model.md) | Maintainer/auditor route | How are persisted facts, proposals, confirmation, and activation bounded? |
| [Installation Troubleshooting](../troubleshooting/installation.md) | Recovery route | Which symptom stops the path, and who owns recovery? |
| [iOS / Android / Java examples](../getting-started/examples/ios.md) | Platform calibration | Which repository evidence and platform boundaries must be collected without claiming a toolchain, device, signing setup, or hosted run? |
| [30-Second Start](../getting-started/30-second-start.md) | Guided entry | What is the shortest wizard path, and what remains afterward? |
| [Standard Adoption Guide](../getting-started/standard-adoption-guide.md) | Adoption lifecycle | How do calibration, Work Items, CI, human approval, and target-project adaptation fit together? |
| [Security and Release Verification](../getting-started/security-release-verification.md) | External evidence boundary | Which release, supply-chain, trust-root, mirror, and enterprise evidence must be verified? |
| [docs/getting-started/first-work-item.md](../getting-started/first-work-item.md) | Getting started | How do I start the first governed task? |
| [docs/philosophy/design-philosophy.md](../philosophy/design-philosophy.md) | Philosophy | Why does AI Cockpit exist, and how does it calibrate trust? |
| [docs/trust-layer.md](../trust-layer.md) | Human-Agent Trust Layer | Why AI Cockpit is needed, what the Human-Agent Trust Layer governs, and how evidence, fail-closed control, trusted chains, supply-chain evidence, and human decisions work together. |
| [docs/architecture.md](../architecture.md) | Architecture | How does the governance evidence flow work? |
| Reference pages | Reference | Where are field, policy, installation, distribution, and troubleshooting details? |
| [docs/configuration.md](../configuration.md) | Configuration reference | Which stack presets and guard settings should I calibrate? |
| [docs/reference/upgrade.md](upgrade.md) | Upgrade guide | How do I move an existing installation forward? |
| [docs/reference/distribution.md](distribution.md) | Distribution reference | What installer options and published integrity capabilities exist? |
| [docs/reference/troubleshooting.md](troubleshooting.md) | Recovery guide | What failed, and how do I recover? |
| [docs/reference/calibration-session.md](calibration-session.md) | Calibration reference | How do the ten stages, confirmations, stale checks, and activation boundary work? |
| [docs/reference/capability-truth-matrix.md](capability-truth-matrix.md) | Truth evidence | Which claims are implemented, template-only, adopter-installed, or planned? |
| [Documentation Context Registry](documentation-context-registry.json) | Context truth | Which plans and design records are current instructions, historical records, implementation records, or immutable archive evidence? |
| [docs/installation.md](../installation.md) | Compatibility entry | Where do old installation links land now? |
| [docs/upgrade.md](../upgrade.md) | Compatibility entry | Where do old upgrade links land now? |
| [docs/distribution.md](../distribution.md) | Compatibility entry | Where do old distribution links land now? |
| [docs/troubleshooting.md](../troubleshooting.md) | Compatibility entry | Where do old troubleshooting links land now? |
| [docs/design-philosophy.md](../design-philosophy.md) | Compatibility entry | Where do old philosophy links land now? |

The Human-Agent Trust Layer is the authoritative Why / What / How explanation. Its complete translations are [中文](../trust-layer.zh-CN.md) and [日本語](../trust-layer.ja.md). The roles remain separate:

- Trust Layer: why AI Cockpit exists, what it governs, and how evidence, fail-closed control, trusted chains, supply-chain evidence, and human decisions work together.
- Design Philosophy: the North Star and design principles.
- Architecture: components and data flow.
- Security and Release Verification: release-level external evidence requirements.
- Capability Truth Matrix: current implementation status; capability must not be inferred from concepts.
- Enterprise Control Checklist: adopter and external-control responsibilities.

## Multilingual adoption map

| Layer | English | 中文 | 日本語 |
| --- | --- | --- | --- |
| Beginner installation | [Installation](../getting-started/installation.md) | [安装](../getting-started/installation.zh-CN.md) | [インストール](../getting-started/installation.ja.md) |
| Strict security route | [Strict verification](../getting-started/installation-security.md) | [严格验证](../getting-started/installation-security.zh-CN.md) | [厳格な検証](../getting-started/installation-security.ja.md) |
| Calibration guide | [Calibration](../getting-started/calibration.md) | [校准](../getting-started/calibration.zh-CN.md) | [校正](../getting-started/calibration.ja.md) |
| Installation recovery | [Troubleshooting](../troubleshooting/installation.md) | [故障排除](../troubleshooting/installation.zh-CN.md) | [トラブルシューティング](../troubleshooting/installation.ja.md) |
| Shortest wizard path | [30-Second Start](../getting-started/30-second-start.md) | [30 秒开始](../getting-started/30-second-start.zh-CN.md) | [30 秒で開始](../getting-started/30-second-start.ja.md) |
| Adoption lifecycle | [Standard Adoption Guide](../getting-started/standard-adoption-guide.md) | [标准采用指南](../getting-started/standard-adoption-guide.zh-CN.md) | [標準導入ガイド](../getting-started/standard-adoption-guide.ja.md) |
| Security/release evidence | [Security and Release Verification](../getting-started/security-release-verification.md) | [安全与发布验证](../getting-started/security-release-verification.zh-CN.md) | [セキュリティとリリース検証](../getting-started/security-release-verification.ja.md) |
| iOS example | [iOS](../getting-started/examples/ios.md) | [iOS](../getting-started/examples/ios.zh-CN.md) | [iOS](../getting-started/examples/ios.ja.md) |
| Android example | [Android](../getting-started/examples/android.md) | [Android](../getting-started/examples/android.zh-CN.md) | [Android](../getting-started/examples/android.ja.md) |
| Java example | [Java](../getting-started/examples/java.md) | [Java](../getting-started/examples/java.zh-CN.md) | [Java](../getting-started/examples/java.ja.md) |

## Split Rules

- Keep the README short enough that a reader can reach the installer in one glance.
- Use README for five-minute positioning, the shortest governance loop, and the Quick Install entry; do not turn it into a complete feature catalogue or Release Reference.
- Keep all three Installation home pages thin, prompt-first, beginner-safe, and semantically aligned: map, prerequisites, six steps, completion, and routes. The first installation ends by starting calibration in a Work Item; an already-installed project starts its needed Work Item directly.
- Keep supply-chain evidence, internal calibration mechanics, recovery variants, and the installation-document maintenance checklist outside the beginner home page.
- Keep iOS, Android, and Java examples complete in all three languages. Detection must never be promoted to toolchain, device, signing, or hosted execution evidence.
- Keep the 30-Second Start, Standard Adoption Guide, and Security and Release Verification complete and semantically aligned in English, Chinese, and Japanese; README entrypoints link to their own language.
- Keep `docs/getting-started/first-work-item.md` focused on the first governed task.
- Keep Philosophy authoritative for why AI Cockpit exists and how calibrated trust, evidence, and responsibility boundaries shape the design.
- Keep the Human-Agent Trust Layer authoritative for Why / What / How, evidence semantics, fail-closed recovery, human decision records, trusted chains, supply-chain evidence, and non-goals.
- Keep Architecture authoritative for repository governance flow, component boundaries, and the Native/Delegated Evidence split.
- Keep Reference pages authoritative for fields, policies, installation, distribution, and troubleshooting.
- Move upgrade, distribution, and recovery details into their own reference pages.
- Keep stack and guard specifics in `docs/configuration.md`, where they can be reused by the install guide without duplicating the full reference.
- Preserve version-neutral guidance where possible, and keep release-specific notes out of the main installation flow.
- Use compatibility entry pages when an older path must continue to resolve.
- Classify every plan and design record in
  [documentation-context-registry.json](documentation-context-registry.json).
  Mutable non-current records display “Historical Record / Not Current Product
  Documentation / Do Not Use As Runtime Instruction.” Immutable Work Item
  archives are classified by the `.ai/work-items/archive/**` registry entry and
  are never rewritten for presentation.

## Intended Navigation

1. Start in [README.md](../../README.md) for the Quick Install entry.
2. Open [docs/getting-started/installation.md](../getting-started/installation.md) for the guided installation and adoption path.
3. Open [docs/getting-started/first-work-item.md](../getting-started/first-work-item.md) when you are ready to start the first governed task.
4. Use [docs/configuration.md](../configuration.md) when you need stack or guard calibration detail.
5. Use [docs/reference/upgrade.md](upgrade.md), [docs/reference/distribution.md](distribution.md), and [docs/reference/troubleshooting.md](troubleshooting.md) as reference pages.
6. Use [docs/philosophy/design-philosophy.md](../philosophy/design-philosophy.md) for the design rationale.

For the interactive flow, link Installation to the Installation Wizard first, then link the Calibration Session reference for the separate ten-stage boundary. Do not use the README or a release note as a substitute for the machine-readable truth matrix.

This page is the navigation map for the documentation system. It explains how the documentation is organized so future edits can stay in the right layer.
