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

各 Work Item は専用 branch と一つの PR を持ちます。`ai-finish` は PR 前に証拠を archive します。provider が merge を報告した後だけ `ai-close-work-item` が archive、Head SHA、base、worktree、remote branch を検証します。

## 停止
gate 失敗、未解決の Unknown、scope 不一致、人の判断不足で停止します。Green だから終了したと推測しません。現在の Work Item を閉じる前に次を始めず、remote failure 後に checkout を削除しません。

## 次
1. [判断状態](../concepts/decision-states.ja.md)
2. [Cockpit Status](../reference/how-to-read-cockpit-status.ja.md)
3. 失敗時は [回復](recovery.ja.md)
