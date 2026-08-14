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

1. **North Star / identity（目指す状態）** — AI Cockpit は、リポジトリに残る証拠を人が確認できる判断へ変え、AI と人の信頼を調整できるようにする仕組みです。[Human-Agent Trust Layer](trust-layer.ja.md) を参照してください。
2. **目的** — 変更の意図、対象範囲、証拠、不明点、人が判断する場所を見えるようにし、Agent が変更内容を勝手に広げないようにします。[AI Cockpit が必要な理由](purpose.ja.md)を参照してください。
3. **設計思想** — 自己申告ではなく証拠を優先し、リスクに応じた確認を行い、証拠が足りなければ安全側で止めます。[設計思想](philosophy/design-philosophy.ja.md)を参照してください。
4. **アーキテクチャ（構造）** — 意図から始まり、Contract（作業契約）、実装、検証、Summary（結果の要約）、Cockpit、そして人の判断へ進む一つの流れです。[アーキテクチャ](architecture.ja.md)を参照してください。
5. **能力と境界** — Cockpit が管理するのはリポジトリの変更証拠です。Agent 実行環境、Workflow Engine、Security Sandbox、認証基盤、人のレビューそのものの代わりにはなりません。[能力と境界](capabilities.ja.md)で責任分担を確認してください。
6. **人の判断** — [判断状態](concepts/decision-states.ja.md)で色の意味を確認し、[Status の読み方](reference/how-to-read-cockpit-status.ja.md)と[ライフサイクル](operations/work-item-lifecycle.ja.md)で、進行・調査・停止の判断を確認します。

## 読者の目的から選ぶ

| 目的 | 入口 | 読了後にできること |
| --- | --- | --- |
| 導入するか決める | [Installation](getting-started/installation.ja.md) | 前提、確認点、作成される証拠を理解する。 |
| 使い始める | [最初の Calibration](getting-started/first-calibration.ja.md) → [最初の Work Item](getting-started/first-work-item.ja.md) | 信頼できる base から最初の範囲付きタスクを始める。 |
| Security 境界を確認する | [Injection Boundary](security/injection-boundary.ja.md) | AI Cockpit の責任と外部 security control の責任を区別する。 |
| 結果を review する | [Quality Gates](operations/quality-gates.ja.md) | Agent の説明を proof とせず、check と証拠を読む。 |
| stop から回復する | [回復](operations/recovery.ja.md) | 不足証拠を直すまで Work Item を保持し、安全に再試行する。 |
| 保守・監査する | [Documentation Architecture](reference/documentation-architecture.ja.md) | canonical owner、言語方針、reference の深さを見つける。 |

この入口では、技術詳細より先に理解の道筋を示します。P0 topic が `planned` の場合は
多言語対応完了を意味せず、後続の文書移行作業を示します。
