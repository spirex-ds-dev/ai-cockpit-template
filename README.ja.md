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

まずは[日本語ドキュメント入口](docs/README.ja.md)から読者向けの道筋を確認してください。

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

判断と回復の道筋は[日本語ドキュメント入口](docs/README.ja.md)にまとめています。

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

現在の主張は [Capability Truth Matrix（英語 fallback、同言語ページ planned）](docs/reference/capability-truth-matrix.md)
に制約されます。

<!-- readme-section: documentation -->
## ドキュメント

[日本語ドキュメント入口](docs/README.ja.md)から、理解、導入、最初の Work Item、
結果の review、stop からの回復、保守・監査の目的を選べます。各ページでは、
同言語の canonical route を優先し、未翻訳の P0 は planned と明示します。
