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
どこで人が判断するか」という4 つの問いを確認します。

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
| 結果を review する | [Quality Gates](operations/quality-gates.ja.md) → [Status の読み方](reference/how-to-read-cockpit-status.ja.md) | Agent の説明を proof とせず、check と証拠を読む。 |
| stop から回復する | [回復](operations/recovery.ja.md) | 不足証拠を直すまで Work Item を保持し、安全に再試行する。 |
| 保守・監査する | [ドキュメント・アーキテクチャ](reference/documentation-architecture.ja.md) | canonical owner、言語方針、reference の深さを見つける。 |

## まず能力一覧を見る

どのページを開けばよいか分からない場合は、まず[能力と境界](capabilities.ja.md)
を見てください。ここが能力の index です。各能力について、目的、現在の status、
責任の境界、詳細ページへのリンクを短く示します。詳細ページでは、前提条件、自然言語の
依頼、使用例、期待する結果、停止・復旧方法、必要な場合だけ advanced command を確認します。

| 目的 | 能力一覧から進む先 |
| --- | --- |
| 完了・warning・blocked の結果を理解する | [Outcome、Summary、Human Benefit Report](features/task-outcome-report.ja.md) |
| 過去に検証された実装を探す | [Implementation Knowledge](reference/implementation-knowledge.ja.md) |
| 独立した Work Item を同時に進める | [Work Item の並行処理](features/work-item-parallelism.ja.md) |
| status、復旧、close を理解する | [Work Item ライフサイクル](operations/work-item-lifecycle.ja.md) |
| 導入、calibration、既存導入の更新を行う | [アップグレード](upgrade.ja.md) |

自然言語の例は、人が Agent に依頼できる目的を示したものです。AI Cockpit 自体は、
範囲付きの repository governance layer です。一文だけで無制限の workflow、scheduler、
外部の proof を作るものではありません。

この入口では、技術詳細より先にプロジェクトを理解する道筋を示します。重要なテーマは
英語・中国語・日本語の入口を優先して整備します。翻訳が未完了、または移行中のページは
その状態を明示し、多言語対応がすべて完了したとは案内しません。現在の境界は、P1 の
commands と schemas の技術リファレンスが英語だけの canonical route であり、P2 の
ドキュメント権威境界リファレンスは既定では翻訳対象外だということです。これは明示された
言語方針であり、すべてのドキュメントの多言語対応が完了したことを意味しません。P0/P1/P2 の正確な方針は
[ドキュメント・アーキテクチャ](reference/documentation-architecture.ja.md)を参照してください。

### 技術リファレンス

次は、保守担当者とコントリビューター向けに言語状態を明示した技術入口です。

- [Commands — 英語の技術リファレンス（P1）](reference/commands.md)
- [Schemas — 英語の技術リファレンス（P1）](reference/schemas.md)
- [ドキュメント権威境界 — 英語のリファレンス（P2、既定では翻訳対象外）](reference/documentation-authority-boundary.md)
