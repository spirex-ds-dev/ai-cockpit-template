---
author: Ray
title: "AI Cockpit をアンインストールする"
description: "プロジェクトから AI Cockpit を削除するための、根拠を残すレビュー可能な手順。"
---

# AI Cockpit をアンインストールする

この回復経路は、プロジェクト担当者が導入済み Runtime を削除すると決めた場合だけに使います。
推測でファイルを削除してはいけません。

<!-- japanese-uninstall: entry -->
1. まずプロジェクトを読むだけで確認し、存在する AI Cockpit ファイルを記録します。

<!-- japanese-uninstall: version-neutral -->
2. 固定した古い版を前提にせず、現在の導入事実を確認します。

<!-- japanese-uninstall: read-only-facts -->
3. 削除前は事実収集だけを行い、プロジェクトへ書き込みません。

<!-- japanese-uninstall: mode-choice -->
4. 担当者に、記録を保存するか完全削除するかを確認します。

<!-- japanese-uninstall: proposal-runtime-zero-write -->
5. 削除計画を作りますが、この段階では実行しません。

<!-- japanese-uninstall: preserve-evidence-default -->
6. 既定では根拠と記録を保存し、無関係なプロジェクト作業を削除しません。

<!-- japanese-uninstall: bounded-confirmation -->
7. 影響ファイル、Unknown、復旧方法をレビューし、実行前に別の確認を得ます。

<!-- japanese-uninstall: detached-execution -->
8. 承認済みの計画だけを、プロジェクト変更から分離した実行として行います。

<!-- japanese-uninstall: receipt-verification -->
9. 削除後に回収証跡を確認し、根拠を保持します。

<!-- japanese-uninstall: stop-recovery -->
10. 所有者、範囲、復旧方法が Unknown なら停止してリポジトリ担当者に相談します。

<!-- japanese-uninstall: purge-separate-confirmation -->
11. 完全削除は保存する削除とは別の確認が必要です。
