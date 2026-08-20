---
author: Ray
title: Task Outcome Report
description: 1 つの governed Work Item が何を変更し、何を見つけ、何を防ぎ、人に何を残すかを evidence から説明します。
audience:
  - adopter
  - reviewer
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - human_benefit_report
  - implementation_approach_report
---

# Task Outcome Report

## この機能でできること

Work Item の終了時に、**何が起き、何を直し、何が残り、次にどの安全な判断をするか**を
確認できます。Task Outcome は evidence に基づく答えです。実行を続けてよいかを示す
Cockpit Status、または PR review 用の任意の表示 Summary とは別のものです。

## 始める前に

Work Item には Contract、Summary、verification evidence、現在の状態が必要です。停止や
Unknown がある場合は、完了と判断する前にその事実を読みます。report は不足した evidence
を補いません。

## 自然言語で依頼する

Agent には次のように依頼できます。

> 「この Work Item が何を届け、どの問題を解決し、どの evidence が結果を支え、どの
> risk が残り、私が次に何を判断する必要があるか説明してください。」

Agent は repository の範囲付き report command を使って答えられます。この文は人と
Agent の interaction pattern であり、fact source、権限、人の決定の証明を作るものではありません。

## 4 つの view と 1 本の evidence chain

| View | 答えること | それではないもの |
| --- | --- | --- |
| Contract | この Work Item に許された、期待されたことは何か。 | 成功の証明。 |
| Summary | 変更・検証中に Agent が何を記録したか。 | raw check や人の判断の代替。 |
| Task Outcome | value、finding、stop、resolution、残存 risk、evidence は何か。 | PR の merge や provider approval の証明。 |
| Human Benefit Report | 人が読む短い結果と次の安全な action は何か。 | 2 つ目の event log や自由な成功 claim。 |

Task Outcome が report projection の machine fact source です。Human Benefit Report は
検証済み Outcome から生成され、事実の claim は `evidenceRefs` に bind されます。

## 使用例：問題から検証済みの解決へ

例えば、Work Item が order service の documentation を直すことを許可されていたとします。

> 「order-service の documentation の問題は直りましたか。merge してよいですか。」

有用な report は次の chain を示します。

```text
Problem: documentation entry が検証済み capability page に届かなかった。
Action: Contract の scope 内で不足していた entry を追加した。
Verification: documentation metadata と internal-link check が passed になった。
Result: evidence 付きの問題は解決した。review/merge は残りの PR と provider evidence
        に基づいて人が判断する。
```

各行には Contract、変更 file、check receipt、Summary の根拠が必要です。「直ったように
見える」だけで reference がなければ inference であり、verified resolution ではありません。

## 使用例：warning または stop

local check が成功していても Hosted CI が未実行なら、その provider evidence の不足を
明示します。Yellow Outcome は待つ、または evidence を取得するという次の action を示します。
Red Outcome は failed gate、原因、場所、evidence、復旧 action を示します。merge 済み、
published、secure、production-ready と推測してはいけません。

## Report の内容

完全な report には Outcome Summary、Task Overview、Delivered Changes、Findings、Risks、
Warnings、Interventions、Forced Stops、Resolutions、Recurrence Prevention、Avoided Impact、
Residual Risks、Human Decisions、Evidence が含まれます。空の section は `None` と明示します。

archive 前に conversational `humanHandoff` を直接渡します。completion、passed checks、
retained work、risk、red reason、人への質問、next action を含みます。evidence reference が
ない claim は inference として扱い、Markdown だけで fact にはしません。

## Report が不完全な場合

欠落、stale、形式不正、別 task、矛盾があれば停止し、source evidence を直します。修正に
新しい path、権限、behavior が Contract の外で必要なら、Contract を amend して再検証するか、
本当に独立した Work Item に分けます。report を編集して問題を隠してはいけません。

## Advanced route

machine source は `.ai/work-items/active/<task>.outcome.json`、派生 Markdown は
`.ai/work-items/active/<task>.outcome.md` です。Review Report は `.ai/cockpit/task_report.json`
と `.ai/cockpit/task_report.md` です。

```sh
make ai-finish TASK=<work-item-id> REPORT_LANGUAGE=ja
make check-ai-task-outcome OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
make check-human-benefit-report OUTCOME=.ai/work-items/active/<work-item-id>.outcome.json
```

`ai-finish` は archive を明示的に要求し、human report を直接渡した後にだけ archive します。
provider が PR merge を報告した後、`make ai-close-work-item TASK=<work-item-id>` が close の
事実を確認してから branch を cleanup します。

## 境界と関連入口

report は platform isolation、enterprise compliance、provider identity、人が読んだ事実、
production readiness、普遍的な security を証明しません。Cockpit Status や元の evidence の
代わりでもありません。

- [Human Benefit Report](human-benefit-report.ja.md)
- [Work Item ライフサイクル](../operations/work-item-lifecycle.ja.md)
- [Decision States](../concepts/decision-states.ja.md)
- [能力一覧と境界](../capabilities.ja.md)
