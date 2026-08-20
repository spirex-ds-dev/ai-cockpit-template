---
author: Ray
title: Human Benefit Report
description: 1 つの governed task の価値、残る risk、次に人が判断することを evidence から短く示します。
audience:
  - adopter
  - reviewer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Human Benefit Report

## この機能でできること

人へ短く、しかし根拠のある答えを渡したい時に使います。**何を完了し、何を見つけ、何を
解決し、どの risk が残り、次に何をするか**を示します。これは検証済み Task Outcome の
human-facing projection です。

## 自然言語で依頼する

> 「この Work Item の human handoff をください。完了、blocking problem、evidence 付きの
> resolution、残る risk、Unknown、人の判断、次の安全な action を含めてください。」

Agent は保存された `humanHandoff` を表示できますが、evidence のない benefit を fact に
書き換えてはいけません。

## 結果の形式

人の判断に使いやすいよう、次の順に表示します。

```text
Task Result
Status: Success / Partial / Blocked / Failed

What was completed
Problems found
Stops triggered
Problems resolved
Risks avoided
Remaining risks
Unknowns
Human decisions
Verification
Impact
Next action
```

finding、risk、warning、forced stop の数は evidence record の数です。生産性、時間、金額、
security、信頼度 score ではありません。

## 使用例

不足していた documentation link を追加した場合、handoff は次のように示します。

```text
Completed: 不足していた capability overview link を追加した。
Resolved problem: docs entry から capability overview に到達できる。
Evidence: Contract、変更 file、passed した documentation-link check。
Remaining risk: Hosted provider review は未確認。
Next action: PR を review し、provider result を待ってから merge する。
```

根拠がない場合は「reported」または「inference」とし、Yellow/Red を維持します。短い要約
だからといって review を省略できるわけではありません。

## 欠落または stale の場合

まず Task Outcome を停止して検証します。欠落、形式不正、stale、別 task、archive 済み
Outcome との不一致は無効です。source record を直して projection を生成し直し、projection
を手編集して完了に見せてはいけません。

## Advanced route と lifecycle

`humanHandoff` は `.ai/work-items/active/<task>.outcome.json` から生成されます。`ai-finish`
は Review Report を `.ai/cockpit/task_report.json` と `.ai/cockpit/task_report.md` に出します。
provider が merge を確認した後、`ai-close-work-item` は branch cleanup 前に Closure Receipt の
隣へ Final Report を作ります。

```sh
make generate-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report \
  OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

Review Report は PR 作成、Hosted CI、merge、cleanup、人が読んだこと、provider identity を
証明しません。Final Report も closure adapter が検証した事実だけを繰り返します。どちらも
platform isolation、enterprise compliance、production safety を証明しません。

[Task Outcome Report](task-outcome-report.ja.md)、[Decision States](../concepts/decision-states.ja.md)、
[Work Item ライフサイクル](../operations/work-item-lifecycle.ja.md)も参照してください。
