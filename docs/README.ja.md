---
author: Ray
title: "AI Cockpit ドキュメント"
description: "AI Cockpit を理解・導入・運用するための読者中心の日本語入口。"
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - documentation_architecture
---

# AI Cockpit ドキュメント

[English](README.md) | [中文](README.zh-CN.md)

ここは AI Cockpit を 5 分で理解するための入口です。実装の詳細を先に読む
必要はありません。まず「何をするプロジェクトか」「なぜ必要か」「何を制御し、
どこで人が判断するか」を確認します。

## プロジェクトを理解する

プロジェクトの North Star から、次の順に読みます。

1. **North Star / identity** — AI Cockpit は、リポジトリの証拠を範囲付きの
   判断に変換し、校正された Human-Agent Trust を支える Repository Governance
   Layer です。[Human-Agent Trust Layer](trust-layer.ja.md) を参照してください。
2. **目的** — Intent、scope、証拠、Unknown、人の判断を見える状態にし、Agent が
   変更内容を勝手に再定義できないようにします。完全な目的ページは P0 移行で
   追加予定です（planned）。
3. **設計思想** — 自己申告より証拠、比例的な control、fail-closed の回復を重視します。
   [Design Philosophy（英語 fallback、同言語ページ planned）](philosophy/design-philosophy.md)
   を参照してください。
4. **アーキテクチャ** — Intent → Contract → Implementation → Verification →
   Summary → Cockpit → Human Decision の一つの流れで構成されます。
   [Architecture](architecture.ja.md) を参照してください。
5. **能力と境界** — Cockpit は証拠を統治しますが、Agent Runtime、Workflow Engine、
   Security Sandbox、identity provider、または人の review の代替ではありません。
   [Capability Truth Matrix（英語 fallback、同言語ページ planned）](reference/capability-truth-matrix.md)
   で現在の主張を確認してください。
6. **人の判断** — [Decision States（英語 fallback、同言語ページ planned）](concepts/decision-states.md)
   で、進行・調査・停止の判断を確認します。

## 読者の目的から選ぶ

| 目的 | 入口 | 読了後にできること |
| --- | --- | --- |
| 導入するか決める | [Installation](getting-started/installation.ja.md) | 前提、確認点、作成される証拠を理解する。 |
| 使い始める | [First Calibration（英語 fallback、同言語ページ planned）](getting-started/first-calibration.md) → [First Work Item](getting-started/first-work-item.ja.md) | 信頼できる base から最初の範囲付きタスクを始める。 |
| 結果を review する | [Quality Gates](operations/quality-gates.ja.md) | Agent の説明を proof とせず、check と証拠を読む。 |
| stop から回復する | [Recovery（英語 fallback、同言語ページ planned）](operations/recovery.md) | 不足証拠を直すまで Work Item を保持し、安全に再試行する。 |
| 保守・監査する | [Documentation Architecture](reference/documentation-architecture.ja.md) | canonical owner、言語方針、reference の深さを見つける。 |

この入口では、技術詳細より先に理解の道筋を示します。P0 topic が `planned` の場合は
多言語対応完了を意味せず、後続の文書移行作業を示します。
