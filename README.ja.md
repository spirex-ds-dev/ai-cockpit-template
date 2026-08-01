---
author: Ray
title: "AI Cockpit"
description: 校正された Human-Agent Trust のための証拠ベースのリポジトリガバナンス。
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
---

# AI Cockpit

[English](README.md) | [中文](README.zh-CN.md)

<!-- readme-section: identity -->
## AI Cockpit とは

AI Cockpit は AI 支援開発のための **Repository Governance Layer** です。
リポジトリの証拠を、人がレビューできる範囲付きの判断に変換します。

詳細は [Human-Agent Trust Layer](docs/trust-layer.ja.md) を参照してください。

<!-- readme-section: problem -->
## 解決する問題

Agent は scope を越え、テストを弱め、検証を省略し、レビュー証拠を残さない
ことがあります。AI Cockpit は意図、実差分、必須検証、Unknown、人の判断を
明示します。

<!-- readme-section: how-it-works -->
## 仕組み

```text
Evidence → Governance Decision → Human Control
```

各変更は 1 つの Contract、branch、Summary/Outcome、PR、検証済み closure を
使います。Agent の説明だけでは証拠になりません。

<!-- readme-section: decision-states -->
## 3 色の判断状態

- **Green:** 必須証拠が、範囲付きの次の操作を支えています。
- **Yellow:** 欠落、古い、矛盾、またはリスクのある証拠を調査します。
- **Red:** 停止します。必須 control の失敗または権限不足があります。

詳細は [Decision States](docs/concepts/decision-states.md) を参照してください。

<!-- readme-section: quick-start -->
## 30 秒で開始

対象 Git project を coding agent で開き、
[30 秒で開始](docs/getting-started/30-second-start.ja.md) に従います。最初は
read-only で、固定 release と write plan を示し、installation 前に確認します。
完全手順は [Installation](docs/getting-started/installation.ja.md) です。

<!-- readme-section: boundary -->
## 製品境界

AI Cockpit は Agent Runtime、Workflow Engine、Security Sandbox、汎用 prompt
injection detector、identity provider、compliance 証明、人の review の代替では
ありません。外部 identity、branch protection、production isolation、release
attestation は外部証拠です。

現在の主張は [Capability Truth Matrix](docs/reference/capability-truth-matrix.md)
に制約されます。

<!-- readme-section: documentation -->
## ドキュメント

- 導入: [Installation](docs/getting-started/installation.ja.md)、[First Calibration](docs/getting-started/first-calibration.md)、[First Work Item](docs/getting-started/first-work-item.ja.md)
- 概念: [Trust Layer](docs/concepts/trust-layer.md)、[Evidence Governance](docs/concepts/evidence-governance.md)、[Decision States](docs/concepts/decision-states.md)
- 運用: [Quality Gates](docs/operations/quality-gates.ja.md)、[Work Item Lifecycle](docs/operations/work-item-lifecycle.md)、[Recovery](docs/operations/recovery.md)
- Security: [Threat Model](docs/security/threat-model.md)、[Injection Boundary](docs/security/injection-boundary.md)、[Supply Chain](docs/security/supply-chain.md)
- Reference: [Schemas](docs/reference/schemas.md)、[Commands](docs/reference/commands.md)、[Documentation Architecture](docs/reference/documentation-architecture.ja.md)
- 履歴: [Plans](docs/archive/plans/README.md)、[Reviews](docs/archive/reviews/README.md)、[Designs](docs/archive/historical-designs/README.md)
