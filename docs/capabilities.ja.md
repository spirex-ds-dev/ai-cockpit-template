---
author: Ray
title: "能力と境界"
description: "AI Cockpit が主張できることと、外部に残る責任を平易に説明する境界 map。"
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, capabilities, boundaries, evidence]
---

# 能力と境界

AI Cockpit の製品境界は **Repository Governance Layer** です。

## Purpose

このページは、**AI Cockpit が何を control し、何を別の人・tool・provider が control するか**に答えます。

## Audience

導入、security review、または repository check が広い性質を証明するか判断する前に読みます。

## Outcome

repository evidence が支える説明、template または adopter の責任、明示的な対象外を区別できます。

## Scenario

adopter が local quality check の成功を見て、production isolation と Agent の identity も証明したのか尋ねました。証明しません。その check は範囲付きの repository 判断を支えるだけで、外部 claim には担当 system の別の evidence が必要です。

## Explanation

### AI Cockpit が統治できること

- Work Item の scope、除外、acceptance、evidence source。
- 登録済み check、change summary、status signal、人の判断、archive traceability。
- gate が決定的に停止または調査を要求できる、既知の repository-local case。

### AI Cockpit だけでは証明できないこと

- Agent Runtime の挙動、汎用 prompt-injection 防御、全言語の semantic safety。
- Security Sandbox の isolation、identity authentication、branch protection、外部の immutable audit。
- 脆弱性がないこと、enterprise compliance、provider publication、production readiness。
- template に材料があることだけを理由にした adopter の installation や calibration。

行単位の現在 status は [Capability Truth Matrix](reference/capability-truth-matrix.md) が source です。`implemented`、`template_only`、`adopter_installed`、`planned` を区別し、prose で広げてはいけません。

```text
local の governance evidence → 範囲付き repository 判断
external/domain evidence → 外部の責任と claim
```

## Action or decision（次に取る行動と判断）

重要な主張（claim）ごとに、誰が evidence を作り、どの範囲を支え、欠落時に安全に取れる次の行動（action）は何かを確認します。この repository が検証できる主張はここで管理し、できないものは外部 owner にリンクします。

## Stop conditions

current evidence がない、`planned` または `template_only` を implemented と表現している、外部責任を local guarantee としている場合は merge または導入判断を停止します。

## Next steps

1. [アーキテクチャ](architecture.ja.md) — evidence の流れと所有者。
2. [Decision States（英語 fallback）](concepts/decision-states.md) — green、yellow、red への対応。
3. [Capability Truth Matrix（英語 fallback）](reference/capability-truth-matrix.md) — 行単位の evidence と制限。

## Technical depth

capability claim は正確な matrix ID と再生成された evidence に bind されます。check の成功は宣言された範囲の evidence であり、普遍的な security や compliance の主張ではありません。Native と Delegated Domain Evidence は分離して保存します。
