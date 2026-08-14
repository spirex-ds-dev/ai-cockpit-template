---
author: Ray
title: "設計思想"
description: "目的のない手続きや複雑性を増やさず、AI Cockpit を形づくる原則。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, design-philosophy, evidence, calibrated-trust]
---

# 設計思想

## Purpose

このページは、**Agent と人が同じ repository を扱うとき、どの原則で control を設計するか**に答えます。

## Audience

新しい process、check、文書を AI Cockpit に加えるべきか判断する人向けです。

## Outcome

校正された信頼、自己申告より証拠、比例的な control、人の責任を重視する理由を理解できます。

## Scenario

team が「安全になるから」と新しい approval form を提案しました。設計思想は先に、どの協働 failure を解決し、どの evidence を生み、誰も維持できない儀式を増やさないかを問います。

## Explanation

### Discover, do not invent

各 component は現実の協働上の必要性に答えなければなりません。checklist が大きいこと自体を理由に process を増やさず、control を risk と evidence に追跡します。

### North Star に従う

North Star は **Calibrated Human-Agent Trust** です。証拠が依存を支えるときは依存し、証拠が欠落、古い、矛盾、または不十分なときは人が介入できる状態を作ります。

### 作る前に収束させる

Architect は解決策を先に固定せず、本質的な構造が見えるまで不要な複雑性を除きます。価値が方向を決め、制約・証拠・実践が最小の構造を明らかにします。

### 異なる責任を尊重する

人は intent、認可、価値判断、最終責任を担います。Agent は実行、分析、一貫性 check、証拠整理に向きます。AI Cockpit は協働を支援しますが、人の判断を代替しません。

### 自己申告より証拠

Agent の説明は理解を助けますが、独立した proof ではありません。test、diff、approval、signature、外部 attestation は、担当する tool または provider が生成した場合にだけ evidence です。

```text
価値 → 原則 → 範囲付き mechanism → evidence → 人の判断
```

## Action or decision

既知の risk と evidence を review しやすくする control は残します。runtime isolation、identity、provider policy、domain 固有の proof が必要なら、担当する専門 tool に委ねます。

## Stop conditions

提案された control に named risk、evidence-producing path、または evidence に見合う claim がない場合は停止します。不確実性を process の言葉で隠して信頼を増やしてはいけません。

## Next steps

1. [アーキテクチャ](../architecture.ja.md) — 原則から生まれる構造。
2. [能力と境界](../capabilities.ja.md) — repository の外に残る責任。
3. [Human-Agent Trust Layer](../trust-layer.ja.md) — 完全な evidence boundary。

## Technical depth

North Star/Mission は Calibrated Human-Agent Trust、認識論的原則は Evidence over Self-Declaration、mechanism は Evidence Governance、製品境界は Repository Governance Layer、実装は Intent、Contract、Verification、Summary、Status、Archive です。
