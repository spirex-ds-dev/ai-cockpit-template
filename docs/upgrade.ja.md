---
author: Ray
title: "アップグレード"
description: "既存の AI Cockpit 導入を安全に更新するための一般ユーザー向け入口。"
audience:
  - adopter
  - contributor
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - repository_governance_layer
keywords: [ai-cockpit, upgrade, compatibility, migration]
---

# アップグレード

## この機能でできること

既に AI Cockpit を導入している project の managed file を更新したい時に使います。
アップグレードは adopter project の独立した Work Item です。command を実行しただけで
calibration や activation が完了したことにはなりません。

## 自然言語で依頼する

> 「既存の AI Cockpit を upgrade する準備をしてください。current/target version、base
> branch、managed file の変更、conflict、rollback evidence、人が判断する場所を先に示してください。」

write の前に Contract、Impact Assessment、target release source、upgrade diff を読みます。
Candidate が正常に activate するまで、現在の Active Configuration を利用できる状態に残します。

## 安全な順序

1. adopter repository の最新の remote default branch から独立した upgrade Work Item を作る。
2. current installation、target release tag、remote、default branch、base commit を記録する。
3. installer に plan と conflict report を作らせ、project-owned governance file を黙って上書きしない。
4. managed file の diff と rollback backup root を確認する。
5. plan と conflict を理解した後だけ write を確認する。
6. adopter の calibration と local check を別の evidence として実行する。
7. 通常の Work Item lifecycle で review、commit、push、merge する。installer は外部 Git 操作を行わない。

## 使用例と期待する結果

依頼：

> 「Candidate が失敗しても current configuration は変更せず、active Work Item または未解決の
> conflict があれば停止してください。」

期待する結果：source/target、Contract/Summary、conflict、rollback backup が明示され、activation
失敗時も以前の Active Configuration が利用できます。

## 停止と recovery

active Work Item がある、remote default branch を決められない、managed file が diverged、
target が downgrade、conflict report が欠落/不正の場合は write 前に停止します。conflict を解消するか
明確な base evidence を用意してから retry します。`--upgrade-with-active` は意図的で別途 review
された recovery の場合だけ使います。

## Advanced route

installer option、release source variable、rollback、conflict report の詳細は[アップグレード技術リファレンス（日本語）](reference/upgrade.ja.md)
を参照してください。command と file の詳細を扱う technical reference です。

installer は commit、push、PR の作成・merge、review branch の削除を行いません。これらは別の
Work Item evidence と人/provider の判断が必要です。

関連入口：[能力一覧と境界](capabilities.ja.md)、[Work Item ライフサイクル](operations/work-item-lifecycle.ja.md)、
[回復](operations/recovery.ja.md)。
