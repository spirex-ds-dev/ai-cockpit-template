---
author: Ray
title: "Work Item の並行処理"
description: "scope、evidence、共有 projection を守りながら独立した Work Item を同時に処理する方法。"
audience:
  - adopter
  - contributor
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
  - work_item_intelligence_interface
keywords: [ai-cockpit, work-item, parallelism, concurrency, evidence]
---

# Work Item の並行処理

## この機能でできること

独立した複数の Work Item を同時に進めたい時に使います。これは **Work Item の並行処理**
であり、evaluation やすべての verification command を並列で実行できるという意味ではありません。

目的は明確です。独立した仕事は同時に進め、file、生成された projection、evidence、
serial な lifecycle 判断を共有する部分は順番に処理します。

## 始める前に

2 つ目の Work Item を dispatch する前に確認します。

- 2 つの目的が本当に独立している。
- それぞれに Contract、branch、worktree、owned scope がある。
- 同じ file や生成 projection を変更しない。
- 相手が作成中の mutable evidence を使わない。
- trusted で明確な base があり、個別に検証できる。
- 人または外部 Agent/Orchestrator が調整する権限を持つ。

## 自然言語で依頼する

Agent には次のように依頼できます。

> 「documentation index の task と独立した calibration reference の task を同時に進めて
> ください。それぞれに Work Item、branch、worktree、scope、evidence、final review を割り当て、
> file や生成 projection が共有される部分は identity を統合せず serial にしてください。」

dispatch、concurrency、retry、provider coordination は Agent/Orchestrator の責任です。
AI Cockpit は各 Work Item の Contract、scope、evidence、verification、Summary、Outcome、
close を管理します。scheduler や retry controller ではありません。

## 何が起きるか

1. coordinator が 2 つの Contract と path/evidence ownership を比較する。
2. 互換性のある Work Item に別々の branch/worktree identity を割り当てる。
3. 各 Agent は owned scope だけで作業し、自分の evidence を記録する。
4. 共有 path、共有 generated output、共有 serial projection は 1 つずつ処理する。
5. 各 Work Item が個別に verification し、自分の Summary と Outcome を作る。
6. coordinator は結果を集計するが、Work Item identity は合体させない。
7. 各 Work Item は通常の PR と `ai-close-work-item` lifecycle で merge/close する。

## 安全な例

```text
Work Item A: docs/getting-started/ の onboarding guide を更新する。
Work Item B: docs/security/ の別の reference page を確認する。

branch、worktree、scope、evidence、PR が分かれているため、
同時に進め、最後に個別に review できる。
```

設定された check graph が許し、同じ mutable evidence を write/read しない場合に限り、
bounded verification が並行になることもあります。これは verification の最適化であり、
Work Item identity の並行結合ではありません。

## 危険な例

```text
Work Item A: docs/reference/capability-truth-matrix.json を再生成する。
Work Item B: その matrix に evidence-bind された capability claim を編集する。

共有されるのは evidence projection です。serial に処理するか、1 つの Work Item が
source-bound change 全体を所有するように ownership を amend します。
```

目的が近いという理由だけで 2 つを同じ branch、worktree、Contract に入れてはいけません。
同じ path を 2 つに割り当てて overlap を隠すこともできません。

## WIII の範囲

Work Item Intelligence Interface（WIII）は current worktree の read-only machine-readable
projection です。Agent が local Work Item intelligence を見るためのもので、scheduler、
DAG engine、retry controller、agent manager、distributed lock、cross-worktree coordinator
ではありません。

外部 Agent/Orchestrator が dispatch と concurrency を担当します。WIII view は別 worktree が
clean であること、provider が PR を merge したこと、人が次の action を approve したことを
証明しません。

## 並行処理が止まった場合

次の場合は停止し、Work Item を分離したままにします。

- path または generated projection が重なる。
- base が incompatible または stale。
- evidence ownership が曖昧。
- 必須 check が shared state を安全な境界なしに変更する。
- Contract にない authority または scope が必要になる。
- 変更 path をどの Work Item が所有するか証明できない。

復旧は、競合部分を serial 化する、scope を変える前に Contract を amend/revalidate する、
または本当に独立した successor を作ることです。盲目的に retry せず、remote failure 後に
checkout を削除しません。

## Advanced route

ownership と bounded verification の詳細は次を参照します。

- [Agent parallel Work Items](../reference/agent-parallel-work-items.md)
- [Safe parallel verification](../reference/safe-parallel-verification.md)
- [Work Item Intelligence Interface](../reference/work-item-intelligence-interface.md)
- [Work Item ライフサイクル](../operations/work-item-lifecycle.ja.md)

current worktree の WIII projection は repository の設定済み status/intelligence entrypoint
から読みます。Contract、verification、PR、close command の代わりではありません。

## 関連入口

- [能力一覧と境界](../capabilities.ja.md)
- [Task Outcome Report](task-outcome-report.ja.md)
- [Recovery](../operations/recovery.ja.md)
