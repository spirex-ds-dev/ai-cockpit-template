---
title: "Cockpit Status の読み方"
description: "生成された status を人の判断へ変換する。"
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Cockpit Status の読み方

## 目的
生成された status を、理解できる範囲付きの判断に変換します。

## 対象
技術者でない承認者を含む、Work Item の確認者。

## 結果
推測せずに結論、証拠、リスク、次の行動を読めます。

## シナリオ
preflight、verification、finish、または gate 失敗の後に status を読みます。

## 判断
`Key Conclusion`、`Recommendation`、`Decision Drivers`、`Evidence`、`Scenario Coverage` の順に確認します。色は score ではありません。

| 色 | 人の判断 | 安全な次の行動 |
| --- | --- | --- |
| Green | review できる証拠がある。進めるか決める。 | 証拠を確認する。merge/release の承認とはみなさない。 |
| Yellow | 残余リスクまたは不足証拠について判断が必要。 | リスクと理由を読み、調査または記録する。 |
| Red | blocker または曖昧さがあり停止が必要。 | 停止し、回復条件に従う。 |
| Unknown | 信頼できる解釈ができない。 | 不足証拠または人の確認を求める。 |

## 停止
status が古い、壊れている、別タスクのもの、証拠不足なら手編集も推測も禁止です。status は Contract、Summary、check の投影です。

## 次
1. [判断状態](../concepts/decision-states.ja.md)
2. [Work Item のライフサイクル](../operations/work-item-lifecycle.ja.md)
3. 停止時は [回復](../operations/recovery.ja.md)
