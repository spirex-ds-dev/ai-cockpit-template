---
author: Ray
title: "AI Cockpit が必要な理由"
description: "AI Cockpit が解決する問題と、人が行う判断を説明する日本語ガイド。"
audience:
  - adopter
  - maintainer
capabilityClaims:
  - repository_governance_layer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
keywords: [ai-cockpit, purpose, north-star, human-agent-trust]
---

# AI Cockpit が必要な理由

## Purpose

このページは、**AI agent が repository を変更する前に、なぜ AI Cockpit を使うのか**を説明します。

## Audience

導入するか判断する人、またはコードを書かない人にプロジェクトを説明する人向けです。

## Outcome

読み終えると、解決する問題、North Star、そして AI Cockpit が統治する範囲と、人・外部 tool が引き続き担う範囲を説明できます。

## Scenario

Agent が小さな文書変更を提案しました。説明はもっともらしい一方、変更できる file、必要な test、branch の安全性が示されていません。AI Cockpit は、変更が team の責任になる前に、その不明点を見えるようにします。

## Explanation

AI 支援開発は速い反面、不確実性を隠すことがあります。Agent は request を誤解し、scope を広げ、check を省略し、reviewer が必要とする証拠なしに自信のある説明をするかもしれません。

AI Cockpit は **Repository Governance Layer** です。人の依頼（request）を範囲付きの Work Item に変換し、意図した scope を確認可能な証拠に結び付けます。証拠が欠落・古い・矛盾している、またはリスクが高いときは、人へ制御（control）を戻します。

North Star は **Calibrated Human-Agent Trust** です。Agent を最大限信頼することではありません。証拠が支えるときは依存し、支えないときは調査・介入・停止を選べる状態にすることです。

仕組みは **Evidence Governance**（証拠の統治）です。AI Cockpit は証拠を管理しますが、test、coverage、SBOM、脆弱性 scan、provenance、signature、provider attestation を生成する専門 tool の代わりにはなりません。

```text
人の意図 → 範囲付き Contract → 変更 → 証拠 → 人の判断
```

## Action or decision

見える scope、再現可能な check、責任ある人の判断が必要な変更には AI Cockpit を使います。Agent Runtime、Workflow Engine、Security Sandbox、identity provider、enterprise compliance が必要な場合は、それを担当する別の tool を選びます。

## Stop conditions

Agent の説明、green に見える status、存在するだけの file を proof として扱わないでください。request、scope、authority、evidence、外部 control が不明なら停止して調査します。

## Next steps

1. [設計思想](philosophy/design-philosophy.ja.md) — control を比例的かつ evidence-led にする原則。
2. [アーキテクチャ](architecture.ja.md) — intent が review 可能な証拠になる流れ。
3. [能力と境界](capabilities.ja.md) — repository が主張できること・できないこと。

## Technical depth

統治される流れは `Intent → Contract → Implementation → Verification → Summary → Cockpit → Human Decision` です。Native Governance Evidence はこの repository が作成し、Delegated Domain Evidence は独立した tool または provider が作成します。完全な境界は [Human-Agent Trust Layer](trust-layer.ja.md) を参照してください。
