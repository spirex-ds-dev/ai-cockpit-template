---
author: Ray
title: "最初の Calibration"
description: "インストール後に、プロジェクトの境界を人が確認する最短の Work Item。"
audience:
  - adopter
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
---

# 最初の Calibration

<!-- capability-claim: project_calibration_profile_proposal -->

Calibration はインストール後に行う、独立した管理対象 Work Item です。プロジェクトの
source、test、generated、protected、quality、ownership、branch、Unknown の境界を、stack
名から推測せずに記録します。

この確認案はテンプレートで提供されます。導入先プロジェクトへのインストール済みであることを証明しません。

1. インストール／導入 Work Item を完了し、close する。
2. 同期した remote default branch から `configure_ai_cockpit` を開始する。
3. `make cockpit-doctor` のリポジトリ証拠を確認する。
4. 比例的な [Calibration Profile](../reference/calibration-profiles.ja.md) を選ぶ。
5. blocking Unknown を解消し、必要な人の確認を得る。
6. Project Profile を確認し、選択した quality route を実行する。

生成された proposal は承認ではありません。詳細は [Calibration Guide](calibration.ja.md) を参照し、完了後は
[最初の Work Item](first-work-item.ja.md) へ進みます。
