---
author: Ray
title: "Java インストール例"
description: 初心者向け Java プロジェクトの AI Cockpit Calibration 例。
keywords: [ai-cockpit, java, maven, gradle, installation]
---

# Java インストール例

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
## Java 用プロンプトをコピーする

```text
段階 1～4、6、7 は読み取り専用で案内してください。段階 5 は設定案
（Candidate）の差分を提案するだけで書き込まず、実際の書き込みは日本語主手順
Step 9 で別途承認します。Maven、Gradle、Wrapper、module、
JDK、profile、unit test、integration test を平易に説明してください。各段階で
確認した根拠、意味、推奨値、未証明事項、期待結果、STOP/連絡先を示してください。
command を創作せず、JDK、build tool、service、credential、network、hosted run を
利用可能と主張しません。今は段階 1 を開始せず、私が主操作表の 1 行目をコピーする
まで待ってください。その後も毎回私の回答を待ちます。
```

例: `pom.xml` は Maven build の記述だけを示し、Maven、必要 JDK、integration
service の動作を証明しません。module mapping 後に `java`、unknown profile は
Java owner へ停止します。

用語: 構成単位（module）、実行構成（profile）、開発ツール一式（toolchain）、
設定案（Candidate）、生成物の未反映差分（generated drift）。

### 主操作表

各回 1 行だけコピーします。

<!-- platform-stage5: proposal-only -->
<!-- platform-step-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 例と選択 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 検出 | 「Maven/Gradle wrapper/manifest、module、toolchain、JDK、source/test、plugin、coverage、生成物、packaging、CI を読み取り専用で列挙してください。」 | `pom.xml` は単一 module や tool 利用可能性の証明ではない。 | module と build 方式の対応が完了。 | 構成が不明。Java 担当者。 |
| 2 開発環境 | 「wrapper、JDK/vendor、mirror、service、credential、network、hosted image の根拠を示してください。」 | JDK 宣言は要件で、local 利用可能性ではない。 | 必要環境に根拠。 | JDK/service/credential/network が不明。Java/CI 担当者。 |
| 3 境界 | 「`java`/`generic`、保守 source/test/resource、target/build/cache/生成物/vendor 除外を提案してください。」 | 混在リポジトリは対応完了まで generic。 | 全パスに担当者。 | 担当者不明。module 担当者。 |
| 4 コマンド | 「files/CI の wrapper lifecycle/task と profile/module/filter/service/coverage、前提、成功/失敗を説明してください。」 | compile/unit/integration/package/publish は別の根拠。 | 出典どおりの正確な command に根拠。 | command 創作/profile/service 不足。Java/build 担当者。 |
| 5 Calibration | 「annotation/schema/client generation、migration、catalog、signing/publishing、security/release、reviewer の Candidate 差分を提案し、書き込み・有効化しないでください。」 | publish は unit test だけで証明しない。 | 提案差分に generator/重要 path が揃う。 | generator/reviewer 不足。build/release owner。 |
| 6 復旧 | 「出力を保持し、JDK/module/profile/service/network/生成物差分の解消後に同じ command を再実行してください。」 | unit は integration の代替不可。 | 同じ command 成功。 | 弱い代替を拒否して STOP。停止した段階に記載の担当者へ連絡し、根拠取得後に同じ段階を再実行。 |
| 7 検証 | 「module/profile、根拠 path/URL、commit SHA、PASS/STOP、不足項目を列にした証拠表を 1 要件 1 行で示し、10 段階、local/hosted、PR Head SHA、人の merge、closure、branch 削除を含めてください。」 | template fixture は導入先の証明ではない。 | 全行がリポジトリ/commit に一致し、欠落がない。 | 根拠不足。repository 担当者。 |

<!-- platform-filled-example: seven-stages -->
### 架空の `SampleOrders` で見る回答例

各行は独立した例です。STOP の行では次へ進みません。担当者の回答を得て同じ段階を
再実行し、PASS を確認して初めて次へ進みます。後続行は解決後の表示例です。

| 段階 | エージェントの回答例 | ユーザーがコピーする回答 | 成功表示 | 停止時に渡す情報 |
| --- | --- | --- | --- | --- |
| 1 | 「Maven Wrapper、`api`/`service` module、unit/integration test を確認」 | `全 module と test 種類を候補一覧にしてください。` | module/build/test の一覧。 | `pom.xml` path を Java 担当者へ渡す。 |
| 2 | 「toolchain は Temurin JDK 21、integration DB は未確認」 | `DB は Unknown のまま停止してください。` | JDK と service の出典行。 | toolchain/service 情報を Java/CI 担当者へ渡す。 |
| 3 | 「`src/main` は保守対象、`target/` は出力。java preset を提案」 | `根拠付き境界に同意します。` | module ごとの含有/除外パス。 | ownership 不明を module 担当者へ渡す。 |
| 4 | 「Wrapper の unit command は CI にあり、integration profile は不明」 | `unit だけ記録し、integration は Unknown のまま STOP してください。build 担当者へ確認後に段階 4 を再実行し、integration test 不要の根拠がある場合だけ not applicable とします。` | exact command、出典、成功条件。 | profile/service を build 担当者へ渡す。 |
| 5 | 「schema generation、migration、publishing は重要」 | `reviewer 付き Candidate 差分だけを提案し、書き込み・有効化しないでください。` | 提案差分に generator/path/reviewer。 | owner 不明を release 担当者へ渡す。 |
| 6 | 「DB 接続失敗」 | `ログを保存し同じ service を用意後、同じ integration command を再実行してください。` | 同じ command が成功。 | log、profile、service を担当者へ渡す。 |
| 7 | 「module/profile CI、PR Head SHA、merge、closure、branch 削除を確認」 | `リンクを一覧にし、欠落がなければ Java adoption PASS としてください。` | 全証拠が同じ commit に対応。 | 欠落と PR URL を repository 担当者へ渡す。 |

以下の 7 小節は表の読み取り専用説明です。第 2 の実行手順として繰り返しません。

<!-- platform-stage: detect-project -->
## 1. プロジェクトを検出する

読み取り専用で Maven/Gradle wrapper・manifest、module、toolchain、JDK declaration、
source/test set、integration-test plugin、coverage、generated source、packaging、CI
を列挙します。single module と仮定しません。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Toolchain evidence を集める

wrapper、必要 JDK/vendor、mirror、service、credential、hosted image を記録します。
`pom.xml`/Gradle file は Maven、Gradle、正しい JDK、network service、secret、
hosted CI の利用可能性を証明しません。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Stack と boundary を選ぶ

証明済み Java layout は `java`、mixed monorepo は module mapping まで `generic`。
保守対象 source/test/resource を特定し、evidence に従い
target/build/cache/generated/vendor を除外します。

<!-- platform-stage: discover-quality-commands -->
## 4. Quality command を発見する

project wrapper を優先し、files/CI から lifecycle/task を取得します。profile、
module、test filter、integration service、coverage output を説明させます。compile、
unit、integration、static analysis、package、publish は別 evidence です。command を創作しません。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Generated/critical path を校正する

annotation/code、schema/client generation、migration、dependency lock/catalog、
signing/publishing、security config、release automation、reviewer を Candidate
項目として提案し、書き込み・有効化しません。

<!-- platform-stage: stop-and-recover -->
## 6. 停止・復旧する

JDK の版が合わない、構成単位（module）または実行設定（profile）が不明、外部
service/認証情報がない、network 接続時しか取得できない依存物がある、生成物に
未反映差分がある場合に停止します。担当者/CI の根拠を得て同じ command を再実行し、integration evidence を unit test で代用しません。

<!-- platform-stage: verify-platform-adoption -->
## 7. Java Adoption を確認する

Calibration 10 段階、module/profile-specific command、local/hosted の別 evidence、
review 済み PR、lifecycle closure が必要です。
