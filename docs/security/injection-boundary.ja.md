---
author: Ray
title: "Injection Boundary"
description: "敵対的または誤解を招く指示に対する、リポジトリレベルの境界。"
audience:
  - adopter
  - security_reviewer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# Injection Boundary

<!-- capability-claim: repository_governance_layer -->

AI Cockpit は汎用の prompt-injection 検出器ではありません。宣言された scope、証拠、権限、保護 path、
operation policy、必要な人の確認と矛盾するリポジトリ操作を拒否または停止できます。

信頼できない文章は、review 可能な証拠と権限に結び付くまでデータです。gate が通っても、宣言された入力と規則だけを
確認したのであり、敵意をすべて検出した証明ではありません。

認証、ホスティング、ネットワーク、依存関係スキャンなどの実際の security control は、対象プロジェクトと外部ツールの責任です。
AI Cockpit は sandbox、identity provider、runtime security の代替ではありません。具体例は[Real Absurd Injection Cases](../reference/real-absurd-injection-cases.ja.md)を参照してください。
