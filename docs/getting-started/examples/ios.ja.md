---
author: Ray
title: "iOS 校正を始める"
description: AI Cockpit のインストール後に使う、iOS プロジェクト向けの簡単な Work Item 校正入口。
keywords: [ai-cockpit, ios, xcode, swift, calibration]
---

# iOS 校正を始める

AI Cockpit のインストール後にこのページを使います。始める前に Xcode、署名、scheme、
または校正の内部仕組みを理解する必要はありません。

<!-- platform-entry: work-item-first -->
## 一度だけコピーする

```text
これは iOS プロジェクトです。校正 Work Item の計画を作成してください。ただし、まだ
ファイルは変更しないでください。リポジトリを読み取り専用で確認し、どの種類の iOS
プロジェクトか、見つけたもの、Unknown のもの、私が確認すべきことを平易な日本語で
示してください。Xcode、scheme、simulator、signing、device、command、CI の事実を
推測しないでください。書き込み前に私の承認を待ってください。
```

## 次に起こること

Agent はレビューできる校正 Work Item を作成します。あなたは計画を確認し、記載された
変更だけを承認します。project file や workspace があるだけでは、Xcode、scheme、
simulator、署名、hosted macOS CI の準備を証明しません。

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## 困ったとき

Work Item が質問する内容は[プロジェクト校正ガイド](../calibration.ja.md)を見てください。
Unknown がある、または確認が停止した場合は[インストールのトラブルシューティング](../../troubleshooting/installation.ja.md)
を使います。Unknown は Unknown のままにし、弱い確認で置き換えません。
