---
title: "Work Item のライフサイクル"
description: "一つの governed change を安全に進める順序。"
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Work Item のライフサイクル

## 目的
control を飛ばさないよう、人と Agent の作業順序を見える化します。

## 対象
Contributor、Maintainer、Reviewer。

## 結果
続行・一時停止・完全な終了の境界を説明できます。

## シナリオ
信頼できる base から merge 後の cleanup まで、一つの変更に使います。

## 判断
`latest remote base → Contract → preflight → implementation → verification → Summary/Outcome → archive → commit/push → PR → merge → closure → cleanup` の順です。

各 Work Item は一つの Contract、専用 branch/worktree、一つの PR に対応します。独立した Work Item は、branch と worktree、宣言した scope、evidence ownership、共有する serialized projection の制約が互換である場合に限り、同時に active にできます。並行実行の編成、集約、projection lease の調整は Agent/Orchestrator が担いますが、governance gate は fail-closed のままです。blocked の Work Item があっても、依存しない互換 Work Item は進められます。Work Item の途中で問題を発見した場合は、認可された scope 内に収まる限り同じ Work Item で解決します。追加の path や権限が必要なら、現在の Contract を先に amend して再検証します。本当に独立した変更である場合、安全な scope 内解決が不可能な場合、またはユーザーが明示した場合に限り、新しい Work Item を作成します。共有 branch-integrated projection は closed projection inventory に従って serialized に扱います。`ai-finish` は PR 前に証拠を archive します。provider が merge を報告した後だけ `ai-close-work-item` が archive、Head SHA、base、worktree、remote branch を検証します。

## 停止
gate 失敗、未解決の Unknown、scope 不一致、互換しない parallel boundary、人の判断不足で停止します。Green だから終了したと推測しません。remote failure 後に Work Item の checkout を削除しません。candidate が closed serialized-projection inventory を欠落または重複させる場合は fail-closed で拒否します。

## 次
1. [判断状態](../concepts/decision-states.ja.md)
2. [Cockpit Status](../reference/how-to-read-cockpit-status.ja.md)
3. 失敗時は [回復](recovery.ja.md)
