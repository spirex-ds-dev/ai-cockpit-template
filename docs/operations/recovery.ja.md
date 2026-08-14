---
title: "回復"
description: "停止・失敗した Work Item を fail-closed で再試行する道筋。"
author: Ray
audience:
  - contributor
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 回復

## 目的
停止を、その場しのぎではなく範囲付きの再試行に変えます。

## 対象
停止した Work Item を担当する Contributor と Maintainer。

## 結果
証拠を保持し、指定された gap を直し、影響した stage だけを再試行できます。

## シナリオ
preflight、verification、hosted verification、closure の停止後に使います。

## 判断
1. 停止理由と回復条件を読む。
2. Contract、Summary、branch、checkout、失敗出力を保持する。
3. scope 内だけを修正し、証拠を更新する。
4. 失敗した gate と宣言済み aggregate check を再実行する。
5. 状態が変わったら再度人の review を求める。

## 停止
gate の bypass、hosted 証拠の代替、別 Work Item の status からの推測、remote failure 後の checkout 削除は禁止です。不明なら停止して確認を求めます。

## 次
1. [判断状態](../concepts/decision-states.ja.md)
2. [Work Item のライフサイクル](work-item-lifecycle.ja.md)
3. installation の症状は [Troubleshooting](../troubleshooting/installation.ja.md)
