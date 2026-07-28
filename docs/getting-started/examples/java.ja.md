---
author: Ray
title: "Java インストール例"
description: 初心者向け Java プロジェクトの AI Cockpit Calibration 例。
keywords: [ai-cockpit, java, maven, gradle, installation]
---

# Java インストール例

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
## Java 用プロンプトをコピーする

```text
段階 1～4、6、7 は読み取り専用で案内してください。段階 5 は設定案
（Candidate）の差分を提案するだけで書き込まず、実際の書き込みは日本語主手順
Step 9 で別途承認します。Maven、Gradle、Wrapper、module、
JDK、profile、unit test、integration test を平易に説明してください。各段階で
確認した根拠、意味、推奨値、未証明事項、期待結果、STOP/連絡先を示してください。
command を創作せず、JDK、build tool、service、credential、network、hosted run を
利用可能と主張せず、毎回待ってください。
```

例: `pom.xml` は Maven build の記述だけを示し、Maven、必要 JDK、integration
service の動作を証明しません。module mapping 後に `java`、unknown profile は
Java owner へ停止します。

用語: 構成単位（module）、実行構成（profile）、開発ツール一式（toolchain）、
設定案（Candidate）、生成物の未反映差分（generated drift）。各回 1 行だけ
コピーします。

<!-- platform-step-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 例と選択 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 検出 | 「Maven/Gradle wrapper/manifest、module、toolchain、JDK、source/test、plugin、coverage、生成物、packaging、CI を読み取り専用で列挙してください。」 | `pom.xml` は単一 module や tool 利用可能性の証明ではない。 | module と build 方式の対応が完了。 | 構成が不明。Java 担当者。 |
| 2 開発環境 | 「wrapper、JDK/vendor、mirror、service、credential、network、hosted image の根拠を示してください。」 | JDK 宣言は要件で、local 利用可能性ではない。 | 必要環境に根拠。 | JDK/service/credential/network が不明。Java/CI 担当者。 |
| 3 境界 | 「`java`/`generic`、保守 source/test/resource、target/build/cache/生成物/vendor 除外を提案してください。」 | 混在リポジトリは対応完了まで generic。 | 全パスに担当者。 | 担当者不明。module 担当者。 |
| 4 コマンド | 「files/CI の wrapper lifecycle/task と profile/module/filter/service/coverage、前提、成功/失敗を説明してください。」 | compile/unit/integration/package/publish は別の根拠。 | 出典どおりの正確な command に根拠。 | command 創作/profile/service 不足。Java/build 担当者。 |
<!-- platform-stage5: proposal-only -->
| 5 Calibration | 「annotation/schema/client generation、migration、catalog、signing/publishing、security/release、reviewer の Candidate 差分を提案し、書き込まないでください。」 | publish は unit test だけで証明しない。 | 提案差分に generator/重要 path が揃う。 | generator/reviewer 不足。build/release owner。 |
| 6 復旧 | 「出力を保持し、JDK/module/profile/service/network/生成物差分の解消後に同じ command を再実行してください。」 | unit は integration の代替不可。 | 同じ command 成功。 | 弱い代替。停止。 |
| 7 検証 | 「10 段階、module/profile の local/hosted、PR Head SHA、人の merge、closure、branch 削除を対応してください。」 | template fixture は導入先の証明ではない。 | リポジトリ/commit に一致。 | 根拠不足。repository 担当者。 |

### 架空の `SampleOrders` で見る回答例

各行は独立した例です。STOP の行では次へ進みません。担当者の回答を得て同じ段階を
再実行し、PASS を確認して初めて次へ進みます。後続行は解決後の表示例です。

| 段階 | エージェントの回答例 | ユーザーがコピーする回答 | 成功表示 | 停止時に渡す情報 |
| --- | --- | --- | --- | --- |
| 1 | 「Maven Wrapper、`api`/`service` module、unit/integration test を確認」 | `全 module と test 種類を候補一覧にしてください。` | module/build/test の一覧。 | `pom.xml` path を Java 担当者へ渡す。 |
| 2 | 「toolchain は Temurin JDK 21、integration DB は未確認」 | `DB は Unknown のまま停止してください。` | JDK と service の出典行。 | toolchain/service 情報を Java/CI 担当者へ渡す。 |
| 3 | 「`src/main` は保守対象、`target/` は出力。java preset を提案」 | `根拠付き境界に同意します。` | module ごとの含有/除外パス。 | ownership 不明を module 担当者へ渡す。 |
| 4 | 「Wrapper の unit command は CI にあり、integration profile は不明」 | `unit だけ記録し integration は Unknown にしてください。` | exact command、出典、成功条件。 | profile/service を build 担当者へ渡す。 |
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
signing/publishing、security config、release automation、reviewer を記録します。

<!-- platform-stage: stop-and-recover -->
## 6. 停止・復旧する

JDK mismatch、unknown module/profile、service/credential 不足、network-only dependency、
generated drift で停止します。owner/CI evidence を得て同じ command を再実行し、integration evidence を unit test で代用しません。

<!-- platform-stage: verify-platform-adoption -->
## 7. Java Adoption を確認する

Calibration 10 段階、module/profile-specific command、local/hosted の別 evidence、
review 済み PR、lifecycle closure が必要です。
