---
title: "判断状態"
description: "証拠から人の判断へ進むための平易なガイド。"
author: Ray
audience:
  - adopter
  - maintainer
capabilityClaims: [repository_governance_layer]
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 判断状態

## 目的
技術者でない読者が、確認・調査・停止のどれを選ぶか判断できるようにします。

## 対象
導入担当、Contributor、Maintainer、Reviewer。

## 結果
状態の意味、人が決めること、安全な次の行動を説明できます。

## シナリオ
check、preflight、finish の後に `.ai/cockpit/current_status.md` を開きます。

## 判断

| 状態 | 意味 | 人の判断 | 安全な次の行動 |
| --- | --- | --- | --- |
| Green | 必要な証拠が新しく、範囲内の行動が支持されている。 | 証拠を確認し、進めるか決める。 | 記載された次の手順へ進む。Green だけで merge/release は承認されない。 |
| Yellow | 証拠が不足・古い・矛盾、または残余リスクがある。 | 調査・リスク記録・停止のどれかを決める。 | 指定された理由を読み、欠落を直すか記録する。 |
| Red | 必須 control が失敗、範囲超過、権限不足のいずれか。 | 停止し、回復条件だけを決める。 | Work Item を保持し、指定された blocker を解決する。 |
| Unknown | 証拠を信頼できる形で解釈できない。 | 進行を決めない。 | 不足する情報または人の確認を求める。 |

## 停止
色から推測しない、別タスクの status をコピーしない、Agent の説明を proof にしないでください。停止には不足する証拠と回復条件を明記します。

## 次
1. [Cockpit Status の読み方](../reference/how-to-read-cockpit-status.ja.md)
2. [Work Item のライフサイクル](../operations/work-item-lifecycle.ja.md)
3. 停止したら [回復](../operations/recovery.ja.md)
