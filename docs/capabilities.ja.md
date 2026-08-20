---
author: Ray
title: "能力一覧と境界"
description: "自然言語のユーザーガイドへ進むための能力 index と、責任の境界を平易に示します。"
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - adopter_capability_manifest
  - adopter_work_item_status_interface
  - adopter_governance_cost_metrics
  - adopter_performance_diagnosis
  - human_benefit_report
  - implementation_approach_report
  - implementation_knowledge_query
  - implementation_knowledge_projection
  - work_item_intelligence_interface
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# 能力一覧と境界

このページは能力一覧です。まず目的、status、責任の境界をざっと確認し、**詳細**の
link を選びます。詳細ページで、自然言語の依頼、使用例、期待する結果、停止・復旧、
必要な場合だけ advanced command を確認します。

## Purpose

このページは、AI Cockpit が人の理解を助ける範囲、各能力が止まる境界、次に開く詳細ページを説明します。

## Audience

adopter、reviewer、maintainer が詳細な使用 path に入る前に能力 map を確認するためのページです。

## Outcome

読み終えると、目的から能力を選び、status と責任の境界を読み、人または外部 system に引き継ぐ条件を確認できます。

## Scenario

以前の実装を知りたい、独立した Work Item を同時に処理したい、停止から回復したい、という目的は分かっていても、どの page や command を使うか分からない場合があります。まず index を読み、Details link を一つ選びます。

AI Cockpit の製品境界は **Repository Governance Layer** です。Work Item の repository evidence を範囲付きの判断へ変えます。Agent Runtime、Workflow Engine、Security Sandbox、identity provider、人の review の代わりではありません。

## Explanation

表の status は adopter capability manifest の語彙です。宣言された surface の状態を
示すもので、普遍的な security、production readiness、provider guarantee ではありません。
[Capability Truth Matrix](reference/capability-truth-matrix.md) に行単位の evidence と制限があります。

| 能力 / 目的 | Manifest status | できること | 境界または owner | 詳細 |
| --- | --- | --- | --- | --- |
| Capability manifest | `implemented` | adopter-facing surface を一つの宣言として確認する。 | template と installer が surface を宣言します。adopter の導入 evidence は別に必要です。 | [Advanced manifest reference](reference/capability-truth-matrix.md) |
| Work Item Status Interface | `adopter_installed` | evidence から生成された Work Item status と index を読む。 | local projection であり、task の実行、schedule、retry はしません。 | [Status Interface](reference/work-item-status-interface.md) |
| Governance cost metrics | `adopter_installed` | Work Item の governance cost の advisory signal を見る。 | local observability の evidence であり、生産性・時間・金額・信頼度 score ではありません。 | [Advanced metrics reference](reference/governance-cost-metrics.md) |
| Performance diagnosis | `adopter_installed` | 記録された時間と bottleneck の手掛かりを見る。 | 記録を診断するだけで、optimization や高速化は約束しません。 | [Advanced diagnosis reference](reference/performance-diagnosis.md) |
| Task Outcome と Human Benefit Report | `adopter_installed` | 何が起き、何が解決し、何が残り、次に安全に何をするかを理解する。 | Outcome が evidence-derived の source で、Human Benefit Report は第二の fact source ではありません。 | [Outcome と report](features/task-outcome-report.ja.md) |
| Implementation Knowledge query | `adopter_installed` | topic、component、date、commit、state の exact filter で過去の Work Item を探す。 | read-only、deterministic、archive-derived です。semantic search や RAG ではありません。 | [Knowledge guide](reference/implementation-knowledge.ja.md) |
| Implementation Knowledge projection | `adopter_installed` | 完了した evidence から検証済みの implementation record と index を作る。 | 通常は dependency map で影響を受ける record だけを更新します。map が欠落または信頼できない場合は明示的な full rebuild/revalidation または fail closed になり、履歴が大きいほどその recovery のコストが増える可能性があります。 | [Knowledge guide](reference/implementation-knowledge.ja.md) |
| Work Item problem-resolution boundary | `adopter_installed` | 発見した問題を現在の Work Item で直すか判断する。 | Contract、authority、base が範囲を支える間は同じ task で直し、別の仕事なら分けます。 | [Lifecycle と recovery](operations/work-item-lifecycle.ja.md) |
| Template Capability Truth material | `template_only` | template が使う evidence model と claim の制限を読む。 | template の材料だけでは adopter の導入、calibration、外部 assurance を証明しません。 | [Capability Truth Matrix](reference/capability-truth-matrix.md) |
| Implementation Approach report | `adopter_installed` | evidence-bound な実装方法の説明を読む。 | Summary、Outcome、Human Benefit Report が持つ reserved reference で、Agent の自己申告ではありません。 | [Outcome と report](features/task-outcome-report.ja.md) |

## Action or decision

| したいこと | 入口 |
| --- | --- |
| 結果を理解して次の判断をする | [Outcome、Summary、Human Benefit Report](features/task-outcome-report.ja.md) |
| 過去に検証された実装を探す | [Implementation Knowledge](reference/implementation-knowledge.ja.md) |
| 独立した Work Item を同時に処理する | [Work Item の並行処理](features/work-item-parallelism.ja.md) |
| status、停止からの recovery、close を理解する | [Work Item ライフサイクル](operations/work-item-lifecycle.ja.md) |
| 導入または既存導入を更新する | [アップグレード](upgrade.ja.md) |

## この index の使い方

最初に command ではなく目的を伝えます。例えば「以前の Work Item が order service の
問題を本当に直したか確認したい」と依頼します。対応する詳細ページで停止条件を先に読み、
再現可能な local check が必要な時だけ advanced command を使います。

自然言語の依頼は、人と Agent の interaction pattern です。Agent が Contract に沿った
command に変換することはできますが、AI Cockpit は scope と repository evidence を確認します。
一文だけで権限、scope、他の Work Item の schedule、外部 proof が生まれることはありません。

## Stop conditions

次の場合は導入・merge・継続の判断を止めます。

- current status または evidence がない、stale、矛盾している、scope 外である。
- `planned` や `template_only` を adopter の current guarantee と表現している。
- 外部 owner の責任を local proof と表現している。
- scheduler、retry controller、identity provider、Security Sandbox、release claim など、
  AI Cockpit の外の能力が必要になっている。

## Next steps

1. [Outcome と report](features/task-outcome-report.ja.md) — 結果と次の安全な action を理解します。
2. [Implementation Knowledge](reference/implementation-knowledge.ja.md) — evidence-bound な過去の実装を探します。
3. [Work Item の並行処理](features/work-item-parallelism.ja.md) — 独立した Work Item を安全に処理します。
4. [Work Item ライフサイクル](operations/work-item-lifecycle.ja.md) — recovery、review、close を確認します。

## Technical depth

英語・中国語・日本語の能力一覧は同じ行、status、境界、詳細 link を保持します。技術
reference の一部は英語だけです。その場合は advanced fallback と明示し、翻訳済みの一般
ユーザーガイドとは扱いません。

証拠の契約は [Capability Truth Matrix](reference/capability-truth-matrix.md)、実装の流れは
[Work Item ライフサイクル](operations/work-item-lifecycle.ja.md)を参照してください。
