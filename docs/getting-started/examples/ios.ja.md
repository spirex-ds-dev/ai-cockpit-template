---
author: Ray
title: "iOS インストール例"
description: 初心者向け iOS プロジェクトの AI Cockpit Calibration 例。
keywords: [ai-cockpit, ios, xcode, swift, installation]
---

# iOS インストール例

[日本語インストール手順](../installation.ja.md)の Step 1～4 を完了します。
platform 段階 1～4 は Installation Step 5～6、書き込みと Adoption の完了処理
（lifecycle closure）は主手順 Step 7～8、段階 5 は Calibration、段階 6 は停止時、
段階 7 は主手順 Step 13 後に使います。本ページは主 lifecycle を置き換えません。

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
## iOS 用プロンプトをコピーする

```text
段階 1～4、6、7 は読み取り専用で案内してください。段階 5 は設定案
（Candidate）の差分を提案するだけで書き込まず、実際の書き込みは日本語主手順
Step 9 で別途承認します。Xcode/Swift 用語を平易に
説明してください。各段階で確認した根拠、意味、Wizard/Calibration 推奨値、
未証明事項、期待結果、STOP/連絡先を示してください。xcodebuild、scheme、
destination、signing、simulator、CocoaPods、hosted CI を創作せず、毎回待ってください。
```

例: `MyApp.xcworkspace` は Xcode workspace の存在だけを示し、Xcode や動く scheme
は証明しません。`swift` preset から開始してプロジェクト固有 command を校正し、
scheme/destination の根拠がなければ iOS 担当者へ確認します。

用語: ビルド対象（scheme）、実行環境（destination）、開発ツール一式
（toolchain）、設定案（Candidate）、生成物の未反映差分（generated drift）。
各回 1 行だけコピーします。

<!-- platform-step-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 例と選択 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 検出 | 「Xcode project/workspace、Package.swift、依存関係、app/extension、scheme、test、CI を読み取り専用で列挙してください。」 | workspace は動く app の証明ではない。 | 構成と担当者が明確。 | 混在・不明。iOS 担当者。 |
| 2 開発環境 | 「Xcode/Swift 版、依存管理、scheme、destination、signing、simulator/device、hosted macOS の根拠を示してください。」 | CI の Xcode 固定はローカル利用可能性と別。 | 全ツール・環境に利用可能性の根拠。 | 版/scheme/destination/signing/host 不足。iOS/release 担当者。 |
| 3 境界 | 「`swift`/`generic` と保守ソース、生成/vendor/出力の除外、根拠を提案してください。」 | `swift` は初期案。non-SPM command は Calibration 必須。 | 全パスを説明できる。 | 初期案が混在構成を隠す。module 担当者。 |
| 4 コマンド | 「repo/CI 出典どおりの正確な command と scheme、destination、configuration、前提、成功/失敗を説明し、創作しないでください。」 | test と archive/signing は別の根拠。 | command と環境に出典がある。 | command/secret/device 不足。iOS/CI 担当者。 |
<!-- platform-stage5: proposal-only -->
| 5 Calibration | 「generator、entitlement、privacy manifest、signing、archive/release、migration、deploy、reviewer の Candidate 差分を提案し、書き込み・有効化しないでください。」 | signing は release reviewer 必須。 | 提案差分に重要/生成 path が揃う。 | owner/再生成 rule 不足。build/release owner。 |
| 6 復旧 | 「失敗の根拠と不足事項/担当者を保持し、根拠取得後に同じ check を再実行してください。」 | 未確認 destination は作業を止める。 | 同じ要件が成功。 | 弱い代替を提案。停止。 |
| 7 検証 | 「10 段階、local/hosted、PR Head SHA、人の merge、closure、branch 削除を対応し、欠落なら未完了としてください。」 | SPM fixture は導入先 Xcode の根拠ではない。 | 本リポジトリ/commit に一致。 | platform/lifecycle の根拠不足。repository 担当者。 |

### 架空の `SampleNotes` で見る回答例

各行は独立した例です。STOP の行では次へ進みません。担当者の回答を得て同じ段階を
再実行し、PASS を確認して初めて次へ進みます。後続行は解決後の表示例です。

| 段階 | エージェントの回答例 | ユーザーがコピーする回答 | 成功表示 | 停止時に渡す情報 |
| --- | --- | --- | --- | --- |
| 1 | 「`SampleNotes.xcworkspace`、app target、unit test target を確認。shared scheme は未確認」 | `shared scheme は Unknown。書き込まず iOS 担当者へ確認してください。` | workspace と target 一覧が表示される。 | 検出した全パスを iOS 担当者へ渡す。 |
| 2 | 「CI は Xcode 16.2、scheme は SampleNotes、destination は iPhone 16 Simulator」 | `その 3 項目を候補として記録し、local availability は別に確認してください。` | project/CI の出典行が表示される。 | version と CI ファイル名を渡す。 |
| 3 | 「`Sources/` は保守対象、`DerivedData/` は出力。swift preset は開始点」 | `提案に同意します。非 SPM command はまだ確定しないでください。` | 含める/除外するパスが別表示。 | 判断不能パスを module 担当者へ渡す。 |
| 4 | 「CI から exact test command を取得。archive/signing command は未確認」 | `test command だけ記録し、archive/signing は Unknown のまま停止してください。` | command の出典、前提、成功表示が並ぶ。 | command と不足項目を CI/release 担当者へ渡す。 |
| 5 | 「entitlement と privacy manifest は重要、signing reviewer は Release Team」 | `Candidate 差分だけを提案し、まだ書き込み・有効化しないでください。` | 提案差分に path と reviewer が表示。 | owner 不明項目を release 担当者へ渡す。 |
| 6 | 「simulator 不在で test 失敗」 | `失敗ログを保存し、同じ destination を用意した後に同じ test を再実行してください。` | 同じ command が成功する。 | failure log、Xcode 版、destination を渡す。 |
| 7 | 「PR #123、Head SHA、hosted check、merge、closure、branch 削除を確認」 | `全項目のリンクを示し、欠落がなければ iOS adoption PASS としてください。` | 7 種の証拠が同じ commit に対応。 | 欠落項目と PR URL を repository 担当者へ渡す。 |

以下の 7 小節は表の読み取り専用説明です。第 2 の実行手順として繰り返しません。

<!-- platform-stage: detect-project -->
## 1. プロジェクトを検出する

読み取り専用で `.xcodeproj`、`.xcworkspace`、`Package.swift`、`Podfile`、
`Cartfile`、scheme、app/extension、unit/UI test target、CI file を列挙させ、SPM-only package と Xcode app/workspace を区別します。

<!-- platform-stage: collect-toolchain-evidence -->
## 2. Toolchain evidence を集める

プロジェクト・CI が宣言する Xcode/Swift version、dependency manager、scheme、signing、
simulator/device 条件を記録します。Xcode file の存在は Xcode、CocoaPods、
simulator、signing identity、hosted macOS CI の利用可能性を証明しません。Unknown はブロックします。

<!-- platform-stage: choose-stack-and-boundaries -->
## 3. Stack と boundary を選ぶ

Swift/Xcode layout は `swift` preset を開始点にし、non-SPM はプロジェクトの根拠で SPM
default command を必ず置換します。mixed repository で Swift preset が誤解を生む
場合だけ `generic`。通常 app/framework source を含め、DerivedData、`.build`、
Pods、generated/vendor は除外します。

<!-- platform-stage: discover-quality-commands -->
## 4. Quality command を発見する

repository/hosted workflow から command をそのまま取得し、scheme、destination、
configuration、前提を説明させます。`xcodebuild`/`pod` を創作しません。unit、
UI/device、archive、signing evidence を分けます。

<!-- platform-stage: calibrate-generated-and-critical-paths -->
## 5. Generated/critical path を校正する

code/project generation、entitlement、signing、privacy manifest、release/archive、
migration、deploy script を記録し、signing/release path に人の reviewer を指定します。

<!-- platform-stage: stop-and-recover -->
## 6. 停止・復旧する

scheme/destination 不明、Xcode/CocoaPods 不在、signing 未解決、dirty generated
files、CI-only secret で停止します。owner から evidence を得て Candidate を更新し、同じ check を再実行します。弱体化しません。

<!-- platform-stage: verify-platform-adoption -->
## 7. iOS Adoption を確認する

Calibration 10 段階、repository-evidenced commands、local/hosted の別結果、review
済み PR、lifecycle closure が必要です。AI Cockpit の最小 SPM fixture は adopter の Xcode app 証拠ではありません。
