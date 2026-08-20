---
author: Ray
title: "Implementation Knowledge"
description: "自然言語を入口に、検証済みで archive から派生した Work Item implementation knowledge を探します。"
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - implementation_knowledge_query
  - implementation_knowledge_projection
keywords:
  - ai-cockpit
  - implementation-knowledge
  - evidence-bound
  - work-item
---

# Implementation Knowledge

## この機能でできること

過去に governed された変更から学びたい時に使います。例えば「order service を扱った
verified な Work Item はどれで、どの file と evidence を残したか」と尋ねます。結果は
検証済みの implementation record を deterministic に探したものであり、Agent の記憶から
自信ありげな答えを作るものではありません。

## 始める前に

Knowledge record は完了した Work Item の evidence から作られます。Contract、Summary、
repository evidence、final Outcome が権威です。Work Item が利用可能な Outcome に到達
していない、または record が欠落・stale の場合、verified な結果はありません。

## record はどのように更新されるか

Work Item が完了すると、AI Cockpit は Knowledge record、query index、dependency map の
3 つの生成 view を維持します。dependency map は各 record を決める Contract、Summary、
Outcome、Evidence の path を記録し、変更された path を影響を受ける Work Item に対応付けます。

通常の Finish または Archive では、この map を使って現在の record と影響を受ける過去の
record だけを更新します。無関係な record は通常 rebuild / rewrite されず、serialized content
が変わった時だけ生成 file が置き換えられます。

これは maintenance の境界であり、すべての recovery が軽いという保証ではありません。
dependency map が欠落、形式不正、stale、または不完全な場合、AI Cockpit は明示的な full
rebuild / revalidation を行うか、fail closed で停止します。full recovery ではより多くの
過去 record を確認することがあるため、Knowledge の履歴が大きくなるほど maintenance の
時間と governance cost も増える可能性があります。query 自体は read-only のままです。更新が
停止したら checker の結果を確認し、record を再利用する前に evidence を修復してください。

## まず自然言語で依頼する

Agent には次のように依頼できます。

> 「orders に関係し、OrderService に影響し、state が verified の Work Item を探して、
> Work Item ID、state、evidence path、次に何を確認すべきかを示してください。」

Agent は依頼を exact filter に変換できます。ただし AI Cockpit の query engine が任意の
自然言語の意味を理解するわけではありません。下の interface は structured、read-only、
conjunctive です。自然言語は HCI の入口で、exact filter と返された record が evidence の境界です。

## 何が起きるか

1. 依頼に明示された topic、component、date、commit、Work Item、state を filter として取り出す。
2. 検証済み index と matching Knowledge record を読む。
3. source path と frozen SHA-256 digest に対して各 record を確認する。
4. Work Item ID と knowledge path の安定した順序で返す。
5. 設計を再利用する前に、record の evidence と limitation を読む。

filter は **AND** で組み合わされます。Work Item ID、topic、component、merged commit、exact
date、inclusive date range、Knowledge state（`verified`、`partial`、`unknown`、`superseded`）
を使えます。

## 使用例：確認可能な結果

依頼：

> 「2026 年 1 月の order-service の変更で、verified だけを表示してください。」

期待する結果：

```text
Query: topic=orders, component=OrderService, date-from=2026-01-01,
       date-to=2026-01-31, status=verified
Matches: 1
Next: 返された knowledgePath と evidenceRefs を開き、新しい Work Item に使う前に確認する。
```

結果が空なら、指定した全 filter を同時に満たす record がないという意味です。repository が
その topic を扱ったことがないという意味ではありません。1 つの exact filter だけを意図的に
広げるか、別の evidence source を人に指定してもらいます。

record が stale、形式不正、矛盾、無効な supersession relationship を持つ場合は、validation
が fail closed になるか、partial/unknown として見える状態を保ちます。新しそうな file を
黙って選んではいけません。

## Knowledge がしないこと

- semantic、vector、fuzzy、RAG search ではありません。
- relevance score、recommendation engine、design authority ではありません。
- Contract、Summary、Outcome、source evidence を上書きする第二の fact source ではありません。
- writer ではありません。query は record、index、report、Work Item を変更しません。
- archive 済みの実装が新しい repository に合うことを保証しません。

date は Contract、Summary、Outcome に明示された時だけ filter できます。file timestamp や
commit history から推測しません。supersession は明示 relationship だけを使い、similarity から
推測しません。legacy record は `partial` のまま残ることがあります。

## Advanced route

source Summary と Outcome が揃った後に record と index を生成します。

```sh
make ai-generate-knowledge \
  TASK=<work-item-id> \
  CONTRACT=.ai/work-items/active/<work-item-id>.contract.json \
  SUMMARY=.ai/work-items/active/<work-item-id>.summary.json \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

record と index を検証します。

```sh
make ai-check-knowledge-index
make check-ai-knowledge
```

exact filter で query します。

```sh
make ai-knowledge-query TOPIC=orders COMPONENT=OrderService STATUS=verified
make ai-knowledge-query DATE_FROM=2026-01-01 DATE_TO=2026-01-31
```

JSON result には normalized query、match count、安定した `results`、互換 alias `matches` が
含まれます。各 result は `workItemId`、`knowledgePath`、`state`、`latestKnownRecord`、
`supersessionStatus`、完全な record を示します。

## 停止条件と関連入口

evidence が欠落、stale、矛盾、または record が宣言した source の外にある場合は停止します。
記憶で穴を埋めず、新しい evidence-bound Work Item を依頼してください。

- [Task Outcome Report](../features/task-outcome-report.ja.md)
- [Human Benefit Report](../features/human-benefit-report.ja.md)
- [能力一覧と境界](../capabilities.ja.md)
- [Work Item ライフサイクル](../operations/work-item-lifecycle.ja.md)
