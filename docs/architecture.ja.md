---
author: Ray
title: "アーキテクチャ"
description: "AI Cockpit が intent を範囲付きの evidence と人の判断へ変換する方法。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, architecture, evidence-flow, boundaries]
---

# アーキテクチャ

## Purpose

このページは、**人の intent がどのように review 可能な repository の判断になるか**に答えます。

## Audience

directory の一覧ではなく、project の map と責任の境界を知りたい adopter、maintainer、reviewer 向けです。

## Outcome

主な flow、evidence の所有者、AI Cockpit の外に残る control を理解できます。

## Scenario

「docs を整理して」と依頼されたとします。編集前に request は scope と acceptance を持つ Contract になります。Agent はその範囲だけを変更し、check が evidence を作り、Summary が結果を圧縮し、人が次の安全な操作を判断します。

## Explanation

```text
Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision
```

1. **Intent:** Work Item の理由と重要な制約を説明します。
2. **Contract:** 編集前に scope、除外、acceptance、evidence source、必須 check を宣言します。
3. **Implementation:** 宣言された repository surface だけを変更します。
4. **Verification:** 登録済み check を実行し結果を記録します。
5. **Summary:** 変更 file、evidence、risk、制限を保存します。
6. **Cockpit:** Repository Truth を Human Decision State に圧縮します。
7. **Human Decision:** proceed、investigate、approve、block、recover を選びます。

Intent、Contract、verification record、Summary、Status、Archive は Native Governance Evidence として repository が所有します。test、coverage、SBOM、脆弱性 scan、provenance、signature、provider attestation は Delegated Domain Evidence で、専門 tool または外部 system が作成します。AI Cockpit はそれを bind・統治できますが、繰り返し表示して真実にすることはできません。

意図的な境界は次の通りです。

```text
Repository Governance Layer | 外部の runtime、identity、sandbox、provider、enterprise control
```

左側は repository change を review 可能にします。右側は adopter、provider、auditor、その他の domain system の責任です。

## Action or decision（次に取る行動と判断）

新しい事実（fact）をどこに置くかを、この流れで決めます。request、scope、verification、人の判断は管理対象の Work Item に置きます。分野固有の証明（proof）は、それを生成できる tool に置き、所有者（ownership）を重複させずリンクします。

## Stop conditions

effect に boundary がない、evidence の所有者が曖昧、または local record を外部 control の proof に使おうとしている場合は停止します。missing link は推測の理由ではなく調査の理由です。

## Next steps

1. [能力と境界](capabilities.ja.md) — local claim と外部責任。
2. [Human-Agent Trust Layer](trust-layer.ja.md) — evidence、fail-closed control、recovery。
3. [Installation](getting-started/installation.ja.md) — 境界を理解した後の導入手順。

## Technical depth

canonical boundary は Work Item Contract、Scope/Backtrack/Coverage/Review Guard、Verification Registry、AI Change Summary、Cockpit Status、Archive Manifest です。一般的な semantic-risk detection、identity authentication、runtime isolation、immutable audit、enterprise compliance を提供するものではありません。
