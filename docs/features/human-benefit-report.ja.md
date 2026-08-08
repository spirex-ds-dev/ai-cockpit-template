---
author: Ray
title: Human Benefit Report
description: 1 つの governed task の価値と残る判断を、証拠から簡潔に示すレポート。
---

# Human Benefit Report

Human Benefit Report は、変更内容、検出された証拠付き問題、停止、解決、回避したリスク、人間の判断、残存リスク、次の安全な操作を短く示します。

Task Outcome が唯一の machine truth です。`ai-finish` は `.ai/cockpit/task_report.json` と `.ai/cockpit/task_report.md` に Review Report を生成し、`check-ai-pr` は archive 済み Outcome との一致を fail closed で検証します。

archive がその Outcome の active path を書き換える場合、archive transaction は正確な report pair を再生成し、両方の path を同じ archive 済み Summary に記録します。その pair を所有できるのは完全な現在の archive transaction だけです。欠落、stale、不正形式、または別 task の report は unowned のままです。

Provider の merge を確認した後、`ai-close-work-item` は branch 削除前に `target/task-closure-receipts/` へ Final Report を生成します。PR URL、merge commit、同期済み base、cleanup intent、継続先だけを provider-bound facts として追加し、`main` を dirty にしません。

問題数は findings、risks、warnings、forced stops の証拠レコード数です。生産性、時間、金額、安全性、信頼度の score ではありません。Review Report は Hosted CI、merge、cleanup、人間の受領、provider identity を証明しません。Final Report も platform isolation、enterprise compliance、production safety を証明しません。
