---
author: Ray
title: "Android インストール例"
description: 初心者向け Android プロジェクトの AI Cockpit Calibration 例。
keywords: [ai-cockpit, android, gradle, installation]
---

# Android インストール例

[日本語インストール手順](../installation.ja.md)の Step 1～4 を完了します。
platform 段階 1～4 は Step 5～6、書き込み/Adoption closure は主手順 Step 7～8、
段階 5 は Calibration、段階 6 は停止時、段階 7 は主手順 Step 13 後に使います。
本ページは lifecycle を置き換えません。

| 日本語主手順 | 本ページで行うこと | 完了後に戻る先 |
| --- | --- | --- |
| Step 1～4 | 何もしない。調査を完了 | Step 5 |
| Step 5～6 | 表の 1～4 行を 1 行ずつコピー | Step 7 |
| Step 7～8 | 何もしない。書き込み/Adoption closure | Step 9 |
| Step 9 | 表の 5 行目をコピー | Step 10 |
| 任意の STOP | 6 行目をコピー | 元の停止段階 |
| Step 13 後 | 7 行目を 1 回だけコピー | Step 14/15 |

<!-- platform-boundary: no-toolchain-device-signing-hosted-claim -->
<!-- platform-prompt: copy-ready -->
## Android 用プロンプトをコピーする

```text
段階 1～4、6、7 は読み取り専用で案内してください。段階 5 は設定案
（Candidate）の差分を提案するだけで書き込まず、実際の書き込みは日本語主手順
Step 9 で別途承認します。Gradle、module、flavor、variant、
JDK、SDK、unit test、device test を平易に説明してください。各段階で確認した根拠、
意味、推奨値、未証明事項、期待結果、STOP/連絡先を示してください。Gradle task を
創作せず、JDK、Android SDK、emulator/device、signing、secret、hosted run を
利用可能と主張せず、毎回待ってください。
```

例: `gradlew` は Gradle Wrapper の存在だけを示し、JDK/Android SDK の導入を
証明しません。module evidence が明確な場合だけ `android`、unknown variant は
Android owner へ停止します。

用語: 構成単位（module）、製品別設定（flavor）、ビルド種別（variant）、
開発ツール一式（toolchain）、設定案（Candidate）、生成物の未反映差分
（generated drift）。各回 1 行だけコピーします。

<!-- platform-step-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 例と選択 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 検出 | 「Wrapper/settings/build/catalog、全 module/flavor/build type/variant、test、manifest、生成物、CI を読み取り専用で列挙してください。」 | `gradlew` は app module 名を証明しない。 | 構成単位とテストの対応が完了。 | module/variant が不明。Android 担当者。 |
| 2 開発環境 | 「Wrapper、AGP、Kotlin、JDK、SDK level、device、signing、credential、CI image の根拠を示してください。」 | Wrapper は JDK/SDK 利用可能性の証明ではない。 | 版と環境に根拠がある。 | JDK/SDK/device/secret 不足。Android/CI 担当者。 |
| 3 境界 | 「`android`/`generic`、各 module の source/test、cache/build/生成物の除外を提案してください。」 | 混在リポジトリは対応完了まで generic 可。 | 全 module に根拠。 | 担当者不明のパス。module 担当者。 |
| 4 コマンド | 「files/CI の Wrapper task と module/flavor/build type/variant、前提、成功/失敗を説明してください。」 | unit/lint/device/release は別の根拠。 | 出典どおりの正確な task に根拠。 | task 創作/variant 不明。Android/CI 担当者。 |
<!-- platform-stage5: proposal-only -->
| 5 Calibration | 「generation、manifest、R8、migration、signing、bundle、permission、privacy/security、reviewer の Candidate 差分を提案し、書き込み・有効化しないでください。」 | release signing は人の reviewer が必要。 | 提案差分に高リスク/生成 path が揃う。 | owner/generator 不足。build/release owner。 |
| 6 復旧 | 「出力を保持し、JDK/SDK/device/secret/生成物差分の根因解消後に同じ Wrapper task を再実行してください。」 | unit は device 根拠の代替不可。 | 同じ task 成功。 | 弱い代替。停止。 |
| 7 検証 | 「10 段階、variant 固有 local/hosted、PR Head SHA、人の merge、closure、branch 削除を対応してください。」 | hosted smoke は導入先 variant の証明ではない。 | リポジトリ/commit に一致。 | 根拠不足。repository 担当者。 |

### 架空の `SampleShop` で見る回答例

各行は独立した例です。STOP の行では次へ進みません。担当者の回答を得て同じ段階を
再実行し、PASS を確認して初めて次へ進みます。後続行は解決後の表示例です。

| 段階 | エージェントの回答例 | ユーザーがコピーする回答 | 成功表示 | 停止時に渡す情報 |
| --- | --- | --- | --- | --- |
| 1 | 「`:app` と `:catalog`、demo/prod flavor、unit/device test を確認」 | `全 module と variant を候補一覧にしてください。まだ task は実行しません。` | module/variant/test の一覧。 | settings/build file 名を Android 担当者へ渡す。 |
| 2 | 「Wrapper 8.9、AGP 8.7、JDK 17、compileSdk 35。SDK/device は未確認」 | `SDK と device は Unknown のまま停止してください。` | 各 version の出典行。 | version 一覧を Android/CI 担当者へ渡す。 |
| 3 | 「`src/main` は保守対象、`build/` は出力。android preset を提案」 | `根拠付き境界に同意します。` | module ごとの含有/除外パス。 | unowned path を module 担当者へ渡す。 |
| 4 | 「CI から `:app:testDemoDebugUnitTest` を取得。device task は未確認」 | `unit task だけ記録し、device evidence は Unknown にしてください。` | exact task、出典、成功条件。 | task と variant を CI 担当者へ渡す。 |
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
bundle、permission、privacy/security config、reviewer を記録します。

<!-- platform-stage: stop-and-recover -->
## 6. 停止・復旧する

JDK/SDK mismatch、unknown variant、device 不在、secret 不足、daemon/cache 不明、
generated drift で停止します。evidence を得て同じ Wrapper task を再実行し、軽い task へ置換して pass にしません。

<!-- platform-stage: verify-platform-adoption -->
## 7. Android Adoption を確認する

Calibration 10 段階、variant-specific command evidence、unit/device と
local/hosted の別結果、review 済み PR、lifecycle closure が必要です。
