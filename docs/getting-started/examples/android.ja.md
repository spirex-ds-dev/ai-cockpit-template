---
author: Ray
title: "Android 校正を始める"
description: AI Cockpit のインストール後に使う、Android プロジェクト向けの簡単な Work Item 校正入口。
keywords: [ai-cockpit, android, gradle, sdk, calibration]
---

# Android 校正を始める

AI Cockpit のインストール後にこのページを使います。始める前に Android SDK、Gradle、
device、署名、または校正の内部仕組みを理解する必要はありません。

<!-- platform-entry: work-item-first -->
## 一度だけコピーする

```text
これは Android プロジェクトです。校正 Work Item の計画を作成してください。ただし、
まだファイルは変更しないでください。リポジトリを読み取り専用で確認し、どの種類の
Android プロジェクトか、見つけたもの、Unknown のもの、私が確認すべきことを平易な
日本語で示してください。SDK、Gradle、module、device、signing、command、secret、CI
の事実を推測しないでください。書き込み前に私の承認を待ってください。
```

## 次に起こること

Agent はレビューできる校正 Work Item を作成します。あなたは計画を確認し、記載された
変更だけを承認します。Gradle file があるだけでは、SDK、wrapper、device、署名、
credential、hosted CI の準備を証明しません。

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-next: calibration-and-recovery -->
## 困ったとき

Work Item が質問する内容は[プロジェクト校正ガイド](../calibration.ja.md)を見てください。
Unknown がある、または確認が停止した場合は[インストールのトラブルシューティング](../../troubleshooting/installation.ja.md)
を使います。Unknown は Unknown のままにし、弱い確認で置き換えません。
