---
author: Ray
title: "Android インストール例"
description: 初心者向け Android プロジェクトの AI Cockpit Calibration 例。
keywords: [ai-cockpit, android, gradle, installation]
---

# Android インストール例

[日本語インストール手順](../installation.ja.md)の Step 1～4 を先に完了します。
このページを上から一度に実行しないでください。現在位置が主手順 Step 5～6 なら
下表の 1～4 行を一行ずつコピーし、完了後は主手順 Step 7 へ戻ります。その他の
位置では、下の対応表に一致する一行だけを使います。

表の用語: 根拠（evidence）、責任者（owner）、確認担当者（reviewer）、署名
（signing）、設定ファイル（manifest）、テスト用データ（fixture）、完全な終了処理
（closure）。エージェントは正式名と日本語の意味を併記します。

下の setup prompt は 1 回だけコピーし、エージェントの案内方法を決めます。その
回答後は **主操作表**から一度に 1 行だけ実行します。後半の記入例は理解用で、
もう一つの実行手順ではありません。

| 日本語主手順 | 本ページで行うこと | 完了後に戻る先 |
| --- | --- | --- |
| Step 1～4 | 何もしない。調査を完了 | Step 5 |
| Step 5～6 | 表の 1～4 行を 1 行ずつコピー | Step 7 |
| Step 7～8 | 何もしない。書き込み/Adoption closure | Step 9 |
| Step 9 | Calibration 内で表の 5 行目を使う | 主手順 Step 9 の残りを完了してから Step 10 |
| platform の 1～5 行が出した STOP | 6 行目をコピー | 元の停止した platform 段階 |
| Step 13 後 | 7 行目を 1 回だけコピー | Step 14/15 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## Android 用プロンプトをコピーする

```text
段階 1～4、6、7 は読み取り専用で案内してください。段階 5 は設定案
（Candidate）の差分を提案するだけで書き込まず、実際の書き込みは日本語主手順
Step 9 で別途承認します。Gradle、module、flavor、build type、variant、
JDK、SDK、unit test、device test を平易に説明し、variant は flavor と build type
から構成される製品構成だと説明してください。各段階で確認した根拠、
意味、推奨値、未証明事項、期待結果、STOP/連絡先を示してください。Gradle task を
創作せず、JDK、Android SDK、emulator/device、signing、secret、hosted run を
利用可能と主張しません。今は段階 1 を開始せず、私が主操作表の 1 行目をコピーする
まで待ってください。その後も毎回私の回答を待ちます。
```

例: `gradlew` は Gradle Wrapper の存在だけを示し、JDK/Android SDK の導入を
証明しません。module evidence が明確な場合だけ `android`、unknown variant は
Android owner へ停止します。

用語: 構成単位（module）、製品別設定（flavor）、ビルド種別（build type）、
flavor と build type の組み合わせで決まる製品構成（variant）、
開発ツール一式（toolchain）、設定案（Candidate）、生成物の未反映差分
（generated drift）。

### 主操作表

各回 1 行だけコピーします。

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 例と選択 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 検出 | 「Wrapper/settings/build/catalog、全 module/flavor/build type/variant、test、manifest、生成物、CI を読み取り専用で列挙してください。」 | `gradlew` は app module 名を証明しない。 | 構成単位とテストの対応が完了。 | module/variant が不明。Android 担当者。 |
| 2 開発環境 | 「Wrapper、AGP、Kotlin、JDK、SDK level、device、signing、credential、CI image の根拠を示してください。」 | Wrapper は JDK/SDK 利用可能性の証明ではない。 | 版と環境に根拠がある。 | JDK/SDK/device/secret 不足。Android/CI 担当者。 |
| 3 境界 | 「`android`/`generic`、各 module の source/test、cache/build/生成物の除外を提案してください。」 | 混在リポジトリは対応完了まで generic 可。 | 全 module に根拠。 | 担当者不明のパス。module 担当者。 |
| 4 コマンド | 「files/CI の Wrapper task と module/flavor/build type/variant、前提、成功/失敗を説明してください。」 | unit/lint/device/release は別の根拠。 | 出典どおりの正確な task に根拠。 | task 創作/variant 不明。Android/CI 担当者。 |
| 5 Calibration | 「generation、manifest、R8、migration、signing、bundle、permission、privacy/security、reviewer の Candidate 差分を提案し、書き込み・有効化しないでください。」 | release signing は人の reviewer が必要。 | 提案差分に高リスク/生成 path が揃う。 | owner/generator 不足。build/release owner。 |
| 6 復旧 | 「出力を保持し、JDK/SDK/device/secret/生成物差分の根因解消後に同じ Wrapper task を再実行してください。」 | unit は device 根拠の代替不可。 | 同じ task 成功。 | 弱い代替を拒否して STOP。停止した段階に記載の担当者へ連絡し、根拠取得後に同じ段階を再実行。 |
| 7 検証 | 「variant、根拠 path/URL、commit SHA、PASS/STOP、不足項目を列にした証拠表を 1 要件 1 行で示し、10 段階、local/hosted、PR Head SHA、人の merge、closure、branch 削除を含めてください。」 | hosted smoke は導入先 variant の証明ではない。 | 全行がリポジトリ/commit に一致し、欠落がない。 | 根拠不足。repository 担当者。 |

<!-- platform-filled-example: seven-stages -->
### 架空の `SampleShop` で見る回答例

各行は独立した例です。STOP の行では次へ進みません。担当者の回答を得て同じ段階を
再実行し、PASS を確認して初めて次へ進みます。後続行は解決後の表示例です。

| 段階 | エージェントの回答例 | ユーザーがコピーする回答 | 成功表示 | 停止時に渡す情報 |
| --- | --- | --- | --- | --- |
| 1 | 「`:app` と `:catalog`、demo/prod flavor、unit/device test を確認」 | `全 module と variant を候補一覧にしてください。まだ task は実行しません。` | module/variant/test の一覧。 | settings/build file 名を Android 担当者へ渡す。 |
| 2 | 「Wrapper 8.9、AGP 8.7、JDK 17、compileSdk 35。SDK/device は未確認」 | `SDK と device は Unknown のまま停止してください。` | 各 version の出典行。 | version 一覧を Android/CI 担当者へ渡す。 |
| 3 | 「`src/main` は保守対象、`build/` は出力。android preset を提案」 | `根拠付き境界に同意します。` | module ごとの含有/除外パス。 | unowned path を module 担当者へ渡す。 |
| 4 | 「CI から `:app:testDemoDebugUnitTest` を取得。device task は未確認」 | `unit task だけ記録し、device evidence は Unknown のまま STOP してください。Android/CI 担当者へ確認後に段階 4 を再実行し、device test 不要の根拠がある場合だけ not applicable とします。` | exact task、出典、成功条件。 | task と variant を CI 担当者へ渡す。 |
| 5 | 「signing、R8、permission、release bundle は重要」 | `reviewer 付き Candidate 差分だけを提案し、書き込み・有効化しないでください。` | 提案差分に path/reviewer 表示。 | owner 不明項目を release 担当者へ渡す。 |
| 6 | 「JDK mismatch で失敗」 | `ログを保存し JDK 17 を用意後、同じ Wrapper task を再実行してください。` | 同じ task が成功。 | log、JDK、task を build 担当者へ渡す。 |
| 7 | 「variant-specific CI、PR Head SHA、merge、closure、branch 削除を確認」 | `リンクを一覧にし、欠落がなければ Android adoption PASS としてください。` | 全証拠が同じ commit に対応。 | 欠落と PR URL を repository 担当者へ渡す。 |

以下の 7 小節は表の読み取り専用説明です。第 2 の実行手順として繰り返しません。

<!-- platform-stage: detect-project -->
## 1. プロジェクトを検出する

読み取り専用で `gradlew`、settings/build/version catalog、module、product
flavor、build type、unit test、`androidTest`、manifest、generated directory、
CI を列挙します。app module が `app` とは仮定しません。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Toolchain evidence を集める

Wrapper/AGP/Kotlin/JDK declaration、SDK level、variant、emulator/device、
signing、credential、CI image を記録します。Gradle Wrapper は JDK、Android
SDK、device、secret、hosted CI の利用可能性を証明しません。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Stack と boundary を選ぶ

証明済み Android layout は `android`、特殊な mixed monorepo は module boundary
校正まで `generic`。各 module の `src/main`、`src/test`、`src/androidTest` を対応し、evidence に従って `.gradle`、`build`、SDK、generated output を除外します。

<!-- platform-stage: discover-quality-commands -->
## 4. Quality command を発見する

files/CI が証明する Wrapper task だけを使い、module、flavor、build type、variant
を特定します。unit、lint、instrumented/device、release build は別 evidence です。task 名を創作しません。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Generated/critical path を校正する

resource/code generation、manifest、ProGuard/R8、migration、signing、release
bundle、permission、privacy/security config、reviewer を Candidate 項目として
提案し、書き込み・有効化しません。

<!-- platform-stage: stop-and-recover -->
## 6. 停止・復旧する

JDK/SDK の版が一致しない、製品構成（variant）が未確認、device がない、必要な
秘密情報がない、常駐プロセス/cache の状態が不明、生成物に未反映差分がある場合に
停止します。根拠を得て同じ Wrapper task を再実行し、軽い task へ置換して pass にしません。

<!-- platform-stage: verify-platform-adoption -->
## 7. Android Adoption を確認する

Calibration 10 段階、variant-specific command evidence、unit/device と
local/hosted の別結果、review 済み PR、lifecycle closure が必要です。
