---
author: Ray
title: "インストール"
description: プログラミング未経験者向けの、プロンプト中心の AI Cockpit 完全導入手順。
keywords:
  - ai-cockpit
  - installation
  - beginner
  - prompt-first
  - ai-agents
---

# インストール

これは英語版の要約ではなく、完全な日本語手順です。プログラミング経験は不要です。
表示されたプロンプトを上から一つずつコピーし、エージェントの結果を確認してください。
エージェントは調査と準備を行えますが、続けるか止めるかを決めるのは常に人です。

導入は、実行基盤の配置、プロジェクト向け調整、変更案のレビュー、外部 CI、
マージ、終了処理の順に進みます。それぞれ別の確認段階です。以下の用語欄で、
対応する正式名称を説明します。

本文で使う用語の平易な意味:

- **Runtime（実行基盤）：**プロジェクトへ配置するガバナンス用ファイルとツール。
- **Calibration（調整）：**共通ルールをこのプロジェクトに合わせる作業。
- **Hosted CI（外部 CI）：**Git サービス側で実行する、PC 外部の検査。
- **Lifecycle closure（完全な終了処理）：**証拠の保管、merge 済み PR の確認、
  base の同期、branch cleanup をまとめた処理。
- **Work Item（作業単位）：**一つの計画と証拠で管理する独立した作業。
- **Session（回答記録）：**保存された調整回答の記録。
- **Candidate（設定案）：**まだ有効化していない設定の提案。
- **Evidence / Owner / Reviewer：**根拠、責任者、別の確認担当者。
- **Full self-check（全項目検査）：**10 件の回答と必須検査が揃ったか確認する処理。
- **SHA-256 / digest（要約値）：**内容の変化を検出するデジタル指紋。
- **Phase record（確認段階の記録）：**Reviewer または Owner の確認を示す記録。
- **Active configuration（現在の設定）：**今実際に有効な設定。
- **Governance Simulation（ガバナンス模擬検査）：**有効化前に設定案の動作を
  安全に確認する検査。

現在の実装範囲は [Capability Truth Matrix](../reference/capability-truth-matrix.md)
で確認してください。最短の入口は [30 秒スタート](30-second-start.ja.md)、
セキュリティとリリース証拠は
[Security and Release Verification](security-release-verification.ja.md)です。

<!-- prompt-safety: read-only-discovery -->
<!-- prompt-safety: explain-evidence-unknowns -->
<!-- prompt-safety: plan-before-write -->
<!-- prompt-safety: human-confirmation-before-write -->
<!-- prompt-safety: no-downstream-authority -->
<!-- prompt-safety: preserve-user-changes -->

## この手順の使い方

各番号で、プロジェクトを開いたエージェントへプロンプトをコピーし、「期待する結果」を確認します。結果が異なる場合や Unknown がある場合は **fail closed（安全側で停止）** とします。承認は現在の段階だけに与え、後続工程をまとめて承認しません。

「Repository」は Git が管理するプロジェクトフォルダー、「Worktree」は現在表示されているファイル、「PR」は変更案を人がレビューするページです。分からない用語は、先に平易な言葉で説明させてください。

この手順は version-neutral です。特定の AI Cockpit 公開版を固定しません。導入ごとに、読み取り専用の調査 prompt が、その時点で根拠を検証できる最新の正式版を動的に選びます。この導入 transaction に固定するのは解決した tag だけです。この手順から固定 tag をコピーしないでください。

## インストール文書の校正チェックリスト

<!-- installation-proofreading-checklist: version-neutral,prompt-first,steps,calibration,platforms,tables,links,lifecycle -->
この手順または翻訳を変更した後は、次の表で校正します。各行に根拠があることを確認してから文書変更を受け入れます。

| 番号 | 校正項目 | 確認する根拠 | PASS | STOP/連絡先 |
| --- | --- | --- | --- | --- |
| 1 | version-neutral の公開表現 | 特定の公開版を固定せず、調査が検証可能な最新正式版を動的に選ぶ。 | 将来の公開版にも手順を再利用できる。 | 固定版または moving main の公開根拠。release 担当者。 |
| 2 | prompt-first 操作 | command の前に目的、期待結果、失敗時の対応を含む prompt がある。 | 初心者が command を創作せず次の依頼をコピーできる。 | command だけ、または説明不足。文書担当者。 |
| 3 | 導入段階の順序 | novice の全段階が一度ずつ正しい順序で存在する。 | 調査から closure まで順番に進められる。 | 段階の欠落・順序違い。導入担当者。 |
| 4 | Calibration の網羅 | 10 段階、Candidate 境界、Unknown のブロッキング、人による確認がある。 | 根拠と承認条件が明確。 | 段階または権限境界の欠落。governance 担当者。 |
| 5 | platform の網羅 | 同じ言語版に iOS、Android、Java の例がある。 | 各 platform に固有の根拠と STOP 経路がある。 | platform 欠落または要約だけ。platform 担当者。 |
| 6 | 表の表示 | 各 decision table に header、separator、連続した正しい列数の行がある。 | Markdown の行結合・列ずれがない。 | 行/列の形式不良。文書担当者。 |
| 7 | link と三言語の整合 | README、関連手順、内部 link、英中日三言語の構成を確認する。 | link が有効で章順と意味が一致する。 | link 切れまたは翻訳 drift。文書担当者。 |
| 8 | lifecycle の根拠 | local/hosted check、PR Head SHA、人の merge、closure、branch cleanup が要求される。 | 全 lifecycle の根拠なしに導入完了としない。 | 根拠欠落または自動 merge の主張。repository 担当者。 |

<!-- novice-stage: before-you-start -->
## 1. 始める前

必要なものは、対象プロジェクト、対象フォルダーを読める AI コーディングエージェント、Git、Python 3.11 以上、GNU Make、既存の Git commit 1 件以上、およびブランチと PR を作成する権限です。AI Cockpit テンプレートリポジトリへ誤って導入しないでください。失えないローカルデータは先にバックアップします。

Git は変更履歴、commit は確認済みの履歴 snapshot、Python と GNU Make は
AI Cockpit の local check に使います。導入済みか分からなくても自分で install
せず、次をコピーします。

```text
AI Cockpit 導入前に、読み取り専用で OS、対象フォルダー、agent access、Git、
Python version、GNU Make、curl、initial commit、branch/PR permission を確認して
ください。各項目を、平易な目的、observed evidence、PASS/STOP、不足時に連絡する
人/チームの表にしてください。未承認の tool installer を提案せず変更もしないでください。
```

期待する結果: 対象プロジェクトと最初の PR のレビュアーが分かっていること。

<!-- novice-stage: open-your-project -->
## 2. プロジェクトを開く

対象フォルダーを AI コーディングエージェントで開きます。まだファイルを作成しません。

次をコピーします。

```text
現在開いているフォルダー、1 つの Git リポジトリのルートか、現在のブランチ、
変更済み・未追跡ファイルの件数だけを示してください。変更は禁止です。各行を
平易な日本語で説明してください。Git ルートでない、AI Cockpit テンプレートを
誤って開いている、既存変更を説明できない場合は STOP。証拠で確認できる場合だけ
プロジェクト責任者を示し、それ以外は Unknown としてください。
```

期待する結果: 正しい Git ルートと変更 0 件、または全既存変更の説明と保持が
確認できます。フォルダーが違う場合は正しいプロジェクトを開き、第 2 段階を繰り返します。

<!-- novice-stage: copy-discovery-prompt -->
## 3. 読み取り専用調査プロンプトをコピーする

次のテキスト全体をコピーします。

<!-- release-metadata-boundary: provider-discovers-latest-verifiable,tag-pinned-verifies-evidence -->
```text
このプロジェクトへ AI Cockpit を導入したいです。最初は読み取り専用で調査してください。
明示的に検証済み private mirror を私が指定しない限り、正規 public source
https://github.com/spirex-ds-dev/ai-cockpit-template.git を使用してください。導入の
たびに正式公開 semantic version を新しい順に確認し、provider release、
tag-pinned metadata、installer、archive asset、digest がすべて揃って相互に一致する
最上位 release を動的に選んでください。version の固定記述、draft/prerelease の
選択、moving `main` metadata の digest authority 利用は禁止です。より新しい正式
release の evidence が不足・不一致なら、失敗項目をすべて表示して STOP し、私の
明示判断後だけ古い検証可能 release を選べます。silent downgrade は禁止です。
この導入で使う release tag を 1 件解決した後、
https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/<resolved-tag>/release.json
を取得し、この tag-pinned metadata だけで tag target、source commit、installer
digest、archive asset、SHA-256 evidence を検証してください。不足・不一致で停止
してください。
作成、編集、削除、commit、push、PR 作成・マージ、公開は禁止です。
関係のないユーザー変更をすべて保持してください。

プログラミング未経験者にも分かる言葉で調査・説明してください。
1. repository root、現在のブランチ、worktree の状態、initial commit の有無
2. remote HEAD が示す default remote/default branch と fetch 後の最新 commit
   （origin/main と仮定しない）
3. Python 3.11+、Git、GNU Make、curl の有無
4. 検出した言語・build system と最適な AI Cockpit stack
5. AGENTS.md、GEMINI.md、CLAUDE.md、Makefile、CI、SECURITY.md、
   CODEOWNERS、active .ai Work Item
6. プロジェクトファイルから証明できる generated files、critical paths、test、
   coverage、quality commands
7. Unknown と推測にすぎない事項

結果を Observed Evidence、Inference、Unknown に分け、技術用語を説明してください。
dirty worktree、initial commit 不在、ツール不足、default branch を証明できない、
active Work Item がある場合は停止して復旧手順を示してください。
問題がなければ Wizard の全選択肢と変更予定ファイルを含む導入計画だけを示し、
私が明示的に承認するまで書き込まないでください。
```

期待する結果: 変更一覧ではなく読み取り専用レポートです。既に変更した場合は停止し、エージェント自身が作ったと証明できる変更だけを戻します。既存のユーザー作業を破棄してはいけません。

最新の正式 release が検証に失敗した場合、勝手に古い版へ変更しません。失敗根拠を
release 担当者がレビューした後だけ、次の限定復旧 prompt をコピーします。

<!-- release-fallback-approval: failed-newer-evidence,owner-review,reverify -->
```text
検証に失敗した新しい正式 release、全失敗 check と根拠、release 担当者の review
記録、この導入で提案する古い tag を示してください。その tag について provider、
tag-pinned metadata、installer、archive、digest の全検証を再実行してください。
全件成功後、この検証済み tag を今回の導入だけに使うか yes/no で 1 件質問します。
書き込み、導入、その他の操作権限は含めません。
```

<!-- novice-stage: review-read-only-report -->
## 4. 調査レポートを確認する

対象フォルダー、既存変更の保護、initial commit、証拠に基づく remote/default
branch、Python と各ツール、プロジェクトに合う stack、明示された Unknown を順番に確認します。

次をコピーします。

```text
上記 7 項目を、何も変更せず 1 件ずつ案内してください。各項目で平易な意味、
確認した根拠、PASS または STOP、STOP 時の連絡先を示してください。現在の項目を
理解したか質問し、私の回答後に次へ進んでください。Unknown を隠さず、導入を
開始しないでください。
```

初心者はコマンドを実行せず、Step 2 の確認プロンプトをもう一度コピーして
worktree（現在のファイル状態）を確認します。

以下は**上級者向け手動 fallback**です。対象プロジェクトの Git ルートでだけ
実行します。目的: 変更済み・未追跡ファイルを表示します。成功: 出力なし、
または理解済みの既存変更だけです。失敗時: 導入せず、各行の説明と保護方法を
エージェントへ依頼します。コマンド終了後は本手順へ戻ります。

<!-- command-guide: purpose,success,failure -->
<!-- command-evidence: adopter_required -->
```sh
git status --short
```

<!-- novice-stage: choose-wizard-options -->
## 5. Wizard mode と installer default をレビューする

現在の対話型 Wizard で人が選ぶのは、**New Adoption（初めて導入する）**、
**Upgrade（導入済み環境を更新する）**、**Dry Run（変更せず計画だけ確認する）**
の三つだけです。初めてなら通常は New Adoption を選びます。

以下の表の技術情報はエージェントと保守担当者が根拠を確認するためのものです。
初心者が CLI option や environment variable を自分で設定する必要はありません。
stack と base/branch は検出され、他は fixed default または CLI/environment
control であり追加画面ではありません。

| 種類 | 項目 | 通常の動作 |
| --- | --- | --- |
| 選択可能 | Mode | 未導入なら **New Adoption**、既存導入の更新だけ **Upgrade**、書き込まず確認するなら **Dry Run**。 |
| 起動時の証拠 | Source | Step 3 で動的に選択した最上位の検証可能な正式 release を使い、解決した tag は今回の導入中だけ変更しません。local clone/private mirror は明示的な非公開 trust path です。 |
| 自動検出 | Stack | Wizard が現在自動検出する信号は Python、Swift、Android です。信号なし・混在構成は `generic` になります。`--stack` はスクリプト実行用で、Wizard の質問ではありません。 |
| 自動検出 | 基準ブランチ（base/branch） | installer がリモートと既定ブランチの根拠から判定し、New Adoption の `--create-adoption` が専用ブランチを作ります。 |
| 固定既定値 | Make 統合 | Wizard では無効（`update_makefile=false`）。`--update-makefile` は競合確認後だけ使用します。 |
| 固定既定値 | Examples | 無効（`with_examples=false`）。example は対象プロジェクトの動作証拠ではありません。 |
| 固定既定値 | Glossary 置換 | 無効（`replace_glossary=false`）。プロジェクト固有内容の置換前に明示レビューが必要です。 |
| 入口 | Interactive | `--interactive` で計画レビューと最終書き込み確認へ進みます。 |

技術 option を自分で解釈せず、先に次をコピーします。

```text
読み取り専用レポートだけから、唯一選択できる Wizard mode と、検出された値
（detected）、固定値（fixed）、コマンド専用設定（CLI-only）を説明してください。
分類、平易な意味、現在値、プロジェクト内の根拠、安全な推奨、停止条件を表で
示してください。
Unknown は推測せず専門家へ確認し、Wizard 実行・書き込みはしないでください。
```

通常は New Adoption、Step 3 で動的に選んだ最上位の検証可能な正式 release
（選択した tag は今回の導入中だけ変更しない）、検出 stack（不確実なら
`generic`）、専用 adoption branch、Make integration なし、既存 glossary 保持、optional examples なし、
interactive review です。既存ファイルや組織ルールと衝突する場合は担当者へ確認します。

保守専用は `--upgrade` と `--upgrade-with-active` です。`--dry-run` は読み取り専用です。`AI_COCKPIT_TEMPLATE_REF` は明示 ref を指定し、`AI_COCKPIT_TEMPLATE_SHA256` は追加 assertion にすぎず、公開メタデータを置き換えません。

この後の手順は **New Adoption** 専用です。**Upgrade** はここで停止し、別 Work
Item で日本語の [Upgrade guide](../reference/upgrade.ja.md) を使います。
**Dry Run** は worktree が変わっていない表示と全計画を review して停止します。
計画が妥当な場合だけこの表へ戻って New Adoption を選びます。Dry Run は導入証拠
ではありません。

<!-- make-entrypoint-boundary: included-makefile-or-explicit-f -->
Wizard は Make integration を既定で無効にします。以後の `make <target>` は、
`include Makefile.ai` を別途 review・導入済みの場合だけ使えます。それ以外は
エージェントが `make -f Makefile.ai <target>` を使い、実際の入口を表示します。
初心者が Makefile を編集したり command を手入力したりする必要はありません。

<!-- make-composite-boundary: selected-entrypoint-propagates-through-ai-finish -->
直接 target と `ai-start`、`ai-finish` などの複合 lifecycle target は、どちらも
明示的な `make -f Makefile.ai <target>` 入口を使えます。AI Cockpit は選択された
repository 内の対応 Makefile を検証し、すべてのネストした Make step へ同じ入口を
伝播します。root Make integration は引き続き任意です。選択ファイルが存在しない、
repository 外にある、未対応名である、または別の `-f` 選択と競合する場合は STOP
し、build/repository 担当者へ連絡します。

モバイル・Java プロジェクトは同じ言語の例を先に開きます:
[iOS](examples/ios.ja.md)、[Android](examples/android.ja.md)、
[Java](examples/java.ja.md)。

<!-- novice-stage: review-installation-plan -->
## 6. 導入計画をレビューする

<!-- installation-plan-release-binding: resolved-tag,metadata,asset,digest,installer,wizard -->
```text
書き込まずに最終導入計画を示してください。動的に解決した stable release tag、
tag-pinned metadata URL、archive asset、検証済み SHA-256、正確な installer
entrypoint と Wizard 起動方法、fetch 後の base commit、新ブランチ、stack、全
installer option、作成・変更・保持する全ファイル、競合、rollback、書き込み後
check を含めてください。installer が使う tag checkout、検証済み installer
digest、別途検証した archive asset が同じ release に binding されることを示し、
archive を installer input と呼ばないでください。各選択がこのプロジェクトに
合う理由を説明してください。
不明は Unknown としてください。
最後は scaffold の書き込みと検証だけを許可する yes/no 質問 1 件にしてください。
commit、push、PR、merge、release、削除、Calibration activation を求めないでください。
```

期待する結果: 正確な計画と限定された確認質問です。moving branch、default
branch の推測、隠れた競合、後続権限の一括要求があれば拒否します。

<!-- novice-stage: approve-scaffold-write -->
## 7. Scaffold 書き込みだけを承認する

計画が正しい場合、記載された install transaction と検証だけを許可します。installer は marker/競合を先に検証し、default base を発見・fetch し、adoption branch を作り、managed files を書きます。途中失敗時は部分導入を rollback します。

期待する結果: 専用 adoption branch と検証レポート。commit、push、PR、merge、release はありません。

承認前に対象 folder、clean worktree、選択した release evidence、fetched default
commit、全変更 file、conflict、rollback を確認し、次をコピーします。

```text
レビュー済み計画どおりの scaffold write と post-write validation だけを承認します。
無関係のユーザー変更を保持し、新 path、conflict、Unknown、validation failure で
停止してください。commit、push、PR、merge、branch 削除、release、Calibration
activation は承認しません。書き込み後は分類済み report を示して待ってください。
```

<!-- novice-stage: inspect-scaffold -->
## 8. Scaffold の全分類を確認する

「分類、path、作成/変更/保持、目的、検証」の表を依頼し、次を確認します。

```text
導入済みのひな形を読み取り専用で、(1) エージェントが読む入口、(2) 用語・方針・
保護・信頼・project profile、(3) adoption の Contract/Summary/start receipt、
(4) scripts/Make、(5) Cockpit Status と根拠、(6) 既存 CI と後続 configuration の
不足、(7) 任意 example の順に確認してください。予定 path と実際の path、状態、
平易な目的、検証、競合からの復旧を表にし、欠落・計画外・無効・競合で STOP。
finish、commit、push、calibration はしないでください。
```

- `AGENTS.md` と任意の Gemini/Claude/Cursor entrypoint
- `.ai/glossary.md`、policy、guard、trust schema、project profile
- active Contract/Summary と start receipt
- `scripts/`、`Makefile.ai`、`Makefile.ai.stack`、Makefile 統合
- `.ai/cockpit/` の status/evidence
- 既存 CI と後続 configuration Work Item が所有する CI 変更（installer は hosted CI を選択・配置しない）、および任意の `examples/`

7 分類を 1 行ずつ確認します。現在の行の依頼だけをコピーしてください。

<!-- scaffold-review-table: copy-request,expected,pass,stop -->
| 分類 | コピーする依頼 | 表示される結果 | PASS | STOP と復旧 |
| --- | --- | --- | --- | --- |
| 1. Agent 入口 | 「導入・保持されたエージェント指示ファイルだけを示し、どのエージェントが読むか説明してください。」 | `AGENTS.md` 等。既存指示は保持またはレビュー済み統合と表示。 | 全パスが計画内で読み手が明確。 | 計画外の置換・指示競合。リポジトリ担当者と計画を修正。 |
| 2. Governance file | 「glossary、policy、guard、trust、Project Profile を示し、既定値と未 Calibration を分けてください。」 | 目的別 `.ai/` パス。既定値がプロジェクト適合済みとは主張しない。 | 必須ファイルが有効で、未 Calibration 項目が明確。 | 欠落・無効・根拠なしの主張。再検証または担当者へ連絡。 |
| 3. Work Item record | 「adoption Contract、Summary、start receipt と全変更への範囲対応を示してください。」 | active `adopt_ai_cockpit` 一式。 | 範囲が adoption の全変更だけを包含。 | 仮入力、欠落、範囲外。先に記録を修正。 |
| 4. Scripts / Make | 「scripts、`Makefile.ai`、`Makefile.ai.stack`、レビュー済み Makefile 変更と各入口を説明してください。」 | Runtime ファイルと Make 統合の有無。 | 検証成功、既存 target 保持。 | 競合、実行不能、計画外変更。競合復旧を実施。 |
| 5. Status / evidence | 「現在の Cockpit Status と導入根拠を再生成せず読み、Contract と差分に比較してください。」 | 既存 `.ai/cockpit/` と現在の Work Item を並べて表示。 | 古さ・欠落・矛盾なし。 | 不一致。再生成計画を示し、別の書き込み承認を待つ。 |
| 6. CI 境界 | 「変更していない既存 CI と後続 configuration の不足点を示し、今は CI を編集しないでください。」 | workflow の根拠と不足点一覧。 | installer が hosted CI を配置・成功したと主張しない。 | 想定外 CI 変更・required Job 不明。保持して CI 担当者へ連絡。 |
| 7. Optional examples | 「examples を依頼したか、全パス、対象プロジェクトの stack の証明ではない理由を示してください。」 | なし、または承認済みパスだけ。 | 選択が計画と一致。 | 未依頼ファイル・能力の過大表現。修正した計画の承認後だけ削除。 |

第 5 行が古い場合は別途コピーします。

```text
Cockpit Status 再生成の正確な command、変更ファイル、期待差分、検証、rollback、
PASS/STOP、リポジトリ担当者を示してください。まだ実行せず、この再生成だけの
yes/no 質問を 1 件示して待ってください。
```

配布元リポジトリの `templates/` と供給元の証拠は、導入先へコピーするファイル
ではありません。ひな形の配置だけでは、プロジェクト調整、品質、外部 CI、
platform toolchain、production readiness の成功を証明しません。

期待する結果: 全 path が説明され adoption Work Item に所有されます。計画外・説明なしの path があれば停止します。

### Calibration 前に Adoption Work Item を完全に閉じる
<!-- lifecycle-order: adoption-close-before-configuration -->

次の判断は必ず分け、一括承認しません。

**A. Local finish と archive だけ:**

```text
adopt_ai_cockpit の local finish だけを実行してください。各 acceptance を変更
file と verification に対応し、Summary、declared checks、before_finish、
ai-finish、全 diff を示します。commit、push、PR、merge、branch 削除、closure、
configuration は禁止し、レビューを待ってください。
```

PASS: archive、diff、全 check が確認できます。STOP: check failure、説明できない
path、acceptance evidence 不足、ユーザー変更の混入。repository owner へ連絡します。

**B. レビュー済み archive の commit だけ:**

```text
レビュー済み adopt_ai_cockpit archive bundle だけの local commit を 1 件承認します。
commit ID と clean worktree evidence を示して停止してください。push、PR、merge、
branch 削除、closure、configuration は承認しません。
```

PASS: local commit が 1 件だけで、worktree は clean、未レビュー path はありません。
STOP: commit に未レビュー path が混入、または adoption 変更が残る場合は repository
owner へ連絡します。

**C. Push と PR 準備を別承認:**

```text
adopt_ai_cockpit branch だけを push し、証明済み default branch 向け PR を準備する
ことを承認します。source branch を保持し、auto-merge/provider 自動削除を無効にし、
PR link、Head SHA、required hosted checks を示して停止。merge/closure は禁止です。
```

PASS: PR の base と Head SHA が正しく、required checks が列挙され、source branch
が保持されています。STOP: push rejection、base/Head SHA 不一致、required check
不足、自動 branch 削除。repository/CI owner へ連絡します。

**D. 人のレビューと merge:** GitHub の **Files changed**、**Conversation**、
**Checks** を人が確認し、required checks 成功後に手動 merge します。

<!-- lifecycle-approval: adoption-closure-plan -->
**E1. Merge 後に closure 計画だけを確認:**

```text
人が adopt_ai_cockpit PR を merge 済みです。最初は読み取り専用で PR ownership、
merged commit、archive evidence、正確な closure command、対象 branch、全検証を
示してください。変更せず、判断を待って停止してください。
```

PASS: ownership、archive、commit、branch、plan が一致。STOP: 不一致を plan/evidence
とともにリポジトリ担当者へ渡します。

<!-- lifecycle-approval: adoption-closure-execute -->
**E2. Closure だけを承認:**

```text
レビュー済み plan に従い adopt_ai_cockpit の lifecycle closure だけを承認します。
ai-close-work-item を実行し、remote/local branch 削除、clean worktree、
fast-forward-only 同期、local default と remote の一致を順番に示して停止。
失敗時は closed と報告せず、local/remote branch の実状態と残存証拠を示します。
branch が既に存在しない場合は、merge 済み PR Head SHA と base の証拠から復旧する
計画を提示し、リポジトリ担当者へ連絡してください。configuration は開始しません。
```

期待する結果: adoption PR が human-merged、`adopt_ai_cockpit` が closed、
remote/local branch が削除され、local default branch が remote と一致します。

<!-- novice-stage: complete-calibration -->
## 9. Calibration の 10 段階をすべて完了する

adoption PR の merge と lifecycle closure を確認した後だけ、別の
`configure_ai_cockpit` Work Item を作ります。エージェントは導入済みの
`cockpit-doctor`、`cockpit-calibrate`、`cockpit-calibrate-session` target を
使います。review 済み Make integration がある場合だけ通常の `make`、
ない場合は `make -f Makefile.ai` をエージェントが使います。
`make cockpit-calibration-wizard` は template maintenance 専用で adopter には
導入されません。初心者は下記 prompt を使い、Session command を手入力しません。
Candidate activation 前に Reviewer と Owner の別々の確認を待ちます。

Calibration Session は Configuration Work Item 内で 10 段階の回答を保存する記録
です。操作はエージェントが行い、利用者は command 入力や JSON 編集をしません。

<!-- calibration-answer-types: yes_no,alternative_input,unknown,not_applicable -->
<!-- calibration-yes-no: type=yes_no,values=Y-or-N -->
回答形式は **yes/no** の machine answer type が `yes_no`、value が `Y` または
`N`、正しい値を示す
**alternative input**、証拠不足で readiness
をブロックする **unknown**、理由必須の **not applicable** の 4 種類です。

<!-- calibration-runtime-boundary: unknown-machine-blocked,confirmations-candidate-bound -->
平易に言うと、Unknown、stale、不完全、または STOP の証拠が 1 件でもあれば
tool は自動停止します。Reviewer と Owner の phase record は、それぞれ準備済み
Candidate の正確な revision と SHA-256 digest を指定しなければなりません。

現在の実装境界: Session はすべての Unknown を残して機械的にブロックし、確認前に
canonical Candidate を 1 つ準備します。回答または証拠の変更後は Candidate と両方の
phase record が無効になり、現在の Candidate identity と一致する 2 つの記録がなければ
activate を拒否します。phase record は判断を内容に結び付けますが、人物の本人性や
役割分離を独立して証明するものではありません。

```text
同期済み default branch から configure_ai_cockpit を開始し、Calibration 10 段階を
順番に案内してください。各段階で、平易な質問、確認 files、observed evidence、
inference、Unknown、回答 type/value、Candidate 変更 file、PASS/STOP、reviewer を
表示します。`yes_no`、alternative_input、unknown、理由付き not_applicable だけを
受け付け、command を創作せず、各段階で私を待ってください。Stage 10 後に Candidate
と inventory を示し、activation 前に Reviewer/Owner を別々に確認します。
commit、push、PR、merge、release、closure は禁止です。
```

<!-- calibration-stage: repository-role -->
1. **Repository role:** application、library、monorepo、template 等と release/deploy 責任。
<!-- calibration-stage: language-and-stack -->
2. **Language and stack:** manifest、version、build tool、preset 選択理由。
<!-- calibration-stage: source-boundaries -->
3. **Source boundaries:** 保守対象 source。vendor/generated/cache/build は除外。
<!-- calibration-stage: test-boundaries -->
4. **Test boundaries:** unit、integration、UI/device、fixture、test-generated を区別。
<!-- calibration-stage: generated-artifacts -->
5. **Generated artifacts:** path、generator、直接編集禁止・再生成ルール。
<!-- calibration-stage: critical-paths -->
6. **Critical paths:** security、release、migration、payment、identity、signing、deploy と reviewer。
<!-- calibration-stage: quality-commands -->
7. **Quality commands:** repository/CI evidence だけから採用し、前提と期待結果を記録。創作禁止。
<!-- calibration-stage: review-requirements -->
8. **Review requirements:** owner、人の reviewer、protected branch、required hosted checks、エージェントに権限がない操作。
<!-- calibration-stage: risks-and-unknowns -->
9. **Risks and unknowns:** 影響、owner、復旧を記録し、証拠不足を N/A に変えない。
<!-- calibration-stage: adoption-readiness -->
10. **Adoption readiness:** blocking fact 解消後、Project Profile を別途レビュー・承認。

各段階で次の依頼を 1 件だけコピーし、結果を見てから回答します。

<!-- calibration-review-table: copy-request,example,pass,stop -->
| 段階 | コピーする依頼 | 根拠の例と平易な意味 | 続行できる状態（PASS） | 停止条件と連絡先（STOP） |
| --- | --- | --- | --- | --- |
| 1 リポジトリの役割 | 「release/deploy ファイルから、アプリ、ライブラリ、複数構成のリポジトリ、テンプレート等のどれかを説明し、公開担当者を示してください。まだ回答を記録しません。」 | release workflow と app manifest は application の提案根拠ですが、最終承認ではありません。 | 役割と公開担当者を示すファイルがあり、説明を理解できる。 | 役割または担当者が不明。リポジトリ担当者へ連絡。 |
| 2 言語と stack | 「設定ファイル、言語版、build/package tool と preset が出発点にすぎない理由、代案を示してください。」 | `pom.xml` は Java/Maven を示唆しますが、必要な JDK の導入済み証明ではありません。 | 版と preset がプロジェクト内の根拠に一致する。 | 混在・特殊構成。platform 担当者へ連絡。 |
| 3 ソース範囲 | 「保守対象ソースと vendor/generated/cache/build を分け、全包含・除外理由を説明してください。」 | `src/main/` は保守対象候補です。`build/` は project evidence が確認して初めて出力扱いです。 | 全パスに担当者と理由がある。 | 保守コードを誤って除外する恐れ。module 担当者へ連絡。 |
| 4 テスト範囲 | 「unit、integration、UI/device、fixture、test-generated と必要環境を分けてください。」 | `src/test` と `src/androidTest` は別の根拠で、互いを代替しません。 | テスト種類と必要環境を画面上で区別できる。 | 種類または環境が不明。test/platform 担当者へ連絡。 |
| 5 生成物 | 「生成パス、generator、正本、再生成方法、直接編集ルールを示してください。」 | schema と generator が既知なら、generated client は正本ではありません。 | generator と差分確認ルールがファイルで確認できる。 | generator 不明。build 担当者へ連絡。 |
| 6 重要パス | 「security、release、migration、payment、identity、signing、deploy、プロジェクト固有の高リスクパスと reviewer を示してください。」 | test 成功後も signing workflow に release owner が必要な場合があります。 | 全重要パスに人の reviewer がいる。 | 担当者不足。security/release 担当者へ連絡。 |
| 7 品質コマンド | 「repo/CI の根拠から正確な command をコピーし、前提、目的、成功表示、失敗対応を説明してください。」 | CI command はその環境での構文を示すだけで、local SDK 導入済みの証明ではありません。 | 全 command に出典と期待表示がある。 | command の創作または前提不足。build/CI 担当者へ連絡。 |
| 8 レビュー要件 | 「CODEOWNERS、branch protection、required hosted checks、agent が承認できない操作を示してください。」 | CODEOWNERS は reviewer の手掛かりで、provider setting が enforcement を証明します。 | 人の担当者と required checks が明確。 | provider の根拠を確認できない。repository 管理者へ連絡。 |
| 9 リスクと不明点 | 「全未解決事項、影響、担当者、復旧を示し、Unknown を N/A にしないでください。」 | required device test で device access がなければ blocking Unknown のままです。 | 続行を妨げる Unknown がない。 | 1 件でも blocking Unknown。記載担当者へ連絡。 |
| 10 導入準備 | 「10 件の回答、proposed configuration、一覧、検査結果、残る制限、予定する Reviewer/Owner を示してください。Stage 10 の回答を保存して full self-check を実行し、confirmation phase record の作成や有効化はまだ行いません。」 | 完全な proposed configuration は reviewable evidence であり、approval ではありません。 | Stage 10 の回答が保存され、full self-check が成功し、将来の Reviewer と Owner が特定済み。 | 根拠の欠落・古さ・却下。該当段階へ戻る。 |

### Calibration 完了記録チェックリスト

この表は人が確認する画面です。
Session は、7 列の確認表に必要な全項目を、段階ごとの記録として保存します。
回答の種類・値・理由は `answer` で保存します。確認した根拠、Candidate の変更案、
`owner` / `reviewer` ラベル、PASS/STOP、判断理由、必要な再確認手順は
`record-evidence` により `checklistEvidence` へ保存します。この 2 つを合わせた
段階ごとの記録が、スキーマで対応する確認項目の正本です。

Work Item には、ガバナンス上の理由、受入条件、Owner の判断、外部レビューの根拠へのリンクを記録します。Session の事実記録を置き換えるものではありません。
保存された `reviewer` / `owner` ラベルは文字列にすぎず、レビュー実施者の本人確認も、独立した役割分離が成立したことも証明しません。
レビュー実施者の本人確認と、独立した役割分離の根拠は Session の外に保存し、
Work Item から参照できるようにします。必要な事実を保存するためのスキーマの正式な
フィールドがない場合は STOP して保存先不足を報告し、存在しない Summary key を
作ったり本文書を手編集したりしません。永続化済み Session で回答と構造化された
根拠の両方を確認した後だけ、その行を完了表示にします。質問しただけでは完了では
ありません。事実または担当者が不足する場合は `unknown` と STOP を選びます。

<!-- calibration-session-persistence-boundary: structured-checklist-evidence,candidate-bound -->
<!-- calibration-session-evidence-boundary: combined-stage-seven-column-record,labels-not-actor-proof -->

governance file を探したり編集したりせず、次の prompt をコピーします。

```text
active configure_ai_cockpit Work Item と永続化済み Calibration Session を特定して
ください。下記 10 行の確認表を使い、現在の段階について observed evidence、
回答 type/value/reason、proposed Candidate change、予定 Owner/Reviewer、理由と
再確認手順を含む PASS/STOP の 1 行案を平易な日本語で示してください。各項目には
「正式名称」「日本語の意味」「私が今判断する内容」を併記し、正確な Session
record を先に示して私の判断を待ちます。
判断後は、`answer` で回答項目と、それに伴う段階の完了状態を保存します。`record-evidence` では、確認した根拠、Candidate の変更案、Owner/Reviewer ラベル、PASS/STOP と判断内容を `checklistEvidence` に保存します。
導入済み Calibration Session interface を使い、Session path と read-only review を表示して schema 対応を証明してください。
field 不足、STOP、Unknown なら停止します。JSON の手編集、根拠の創作、Candidate
prepare/activate、commit、push、PR 作成・merge、release、Work Item close は
禁止です。
```

<!-- calibration-completion-checklist: state,evidence,answer,candidate,owner-reviewer,pass-stop -->
| 表示用の段階名（stage label）と確認項目 | 完了状態 | 記録する確認根拠（observed evidence） | 記録する回答の種類/値（type/value） | 記録する設定案の変更（Candidate） | 記録する責任者 / 確認担当者（Owner / Reviewer） | 記録する判定 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. repository-role — リポジトリの役割と公開責任 | [ ] | 確認した release/deploy file と観察した役割を記録：___ | `yes_no`、`alternative_input`、`unknown`、または理由付き `not_applicable` を記録：___ | Candidate の role field、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 2. language-and-stack — 言語、版、tool、preset 適合 | [ ] | manifest、version file、build/package の根拠を記録：___ | 回答 type と正確な stack/version 値を記録：___ | Candidate の stack field、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 3. source-boundaries — 保守対象と除外 path | [ ] | 確認した source、vendor、generated、cache、output path を記録：___ | 回答 type と正確な include/exclude 値を記録：___ | Candidate の source-boundary diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 4. test-boundaries — Test 種別、fixture、環境 | [ ] | unit/integration/UI/device/fixture の根拠と必要環境を記録：___ | 回答 type と正確な test-boundary 値を記録：___ | Candidate の test-boundary diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 5. generated-artifacts — Generator と再生成 rule | [ ] | generated path、source of truth、generator、再生成の根拠を記録：___ | 回答 type と正確な generator/editing rule を記録：___ | Candidate の generated-artifact diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 6. critical-paths — 高リスク path と人の review | [ ] | security/release/migration/signing/deploy path と根拠を記録：___ | 回答 type と正確な critical-path 値を記録：___ | Candidate の critical-path diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 7. quality-commands — 出典のある正確な command と前提 | [ ] | repo/CI 出典、正確な command、前提、期待結果を記録：___ | 回答 type と出典のある正確な command set を記録：___ | Candidate の quality-command diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 8. review-requirements — Owner、保護、hosted checks | [ ] | CODEOWNERS/provider/CI の根拠と確認不能な provider fact を記録：___ | 回答 type と正確な review requirement を記録：___ | Candidate の review-policy diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 9. risks-and-unknowns — 影響、担当者、復旧 | [ ] | 各 risk/Unknown、影響、owner、復旧の根拠を記録：___ | 回答 type を記録し、証拠不足を N/A に変更しない：___ | Candidate の risk/Unknown diff、または理由付き `no change` を記録：___ | Owner：___；Reviewer：___ | `PASS`—理由、または `STOP`—不足根拠、Owner、再確認手順を記録：___ |
| 10. adoption-readiness — Proposed configuration、inventory、checks、将来の判断 | [ ] | 最新 proposed-configuration/inventory/check の根拠と残る制限を記録：___ | 有効化せず最終回答 type/value を記録：___ | proposed Candidate change と configuration 識別子を記録：___ | 予定する Owner：___；予定する Reviewer：___；まだ confirm しない | 回答が保存され full self-check が成功した後だけ `PASS`、それ以外は `STOP` を記録し、phase record は次の独立した手順で作成：___ |

confirmation 前に scaffold review から引き継いだ CI gap を全件閉じます。

<!-- calibration-ci-gap-boundary: plan,approval,implementation,verification -->
```text
close 済み adoption Work Item の CI gap list を読み、各項目の repository 根拠、
owner、正確な Candidate diff または根拠付き no-change 理由、validation、必要な
hosted evidence、rollback、PASS/STOP を示してください。書き込みが必要なら、
その正確な CI diff だけを対象に yes/no で 1 件質問して待ちます。承認後はその
diff だけを実装し local validation を示し、後続 PR で同一 commit の hosted
evidence を取得します。required CI 項目が Unknown・未実装・未検証なら
Calibration の confirmation/activation を行いません。
```

### Activation を別に review・承認する

10 行の check は Candidate が review 可能という意味で、activation ではありません。
Session は各行の 7 列を完全な構造化 evidence として保存しますが、`reviewer` と
`owner` という phase 名は人物の身元を証明しません。先に Reviewer と Owner を
特定し、人物・役割の外部根拠を保存する Work Item review 位置を確認します。次に
review、full self-check、Governance Simulation、`prepare-candidate` の順で実行
してから、次の prompt で 2 件の判断を別々に取得・記録します。

<!-- calibration-confirmation-boundary: phase-records,external-actor-identity -->
```text
activate しないでください。導入済み Calibration Session interface で、永続化
Session ID/path、prepared Candidate revision、SHA-256 digest、正確な
configuration、10 行の構造化 checklist evidence を表示してください。現在の
操作者である私が、その正確な review package を特定済み Reviewer へ先に渡し、
その人の明示判断と外部の本人確認根拠を返します。それまで待ちます。次に Owner
へ別に同じ手順を行います。本人の判断を受け取った後だけ、表示済みの正確な
revision/digest を指定して各 phase を記録します。digest-bound の 2 phase record
と人物・役割分離を示す Work Item の外部根拠を表示してください。Session が
binding するのは判断と Candidate 内容であり、人物を認証しないと明記します。
不足・古い・却下・digest 不一致・同一人物の判断なら STOP します。
```

次に読み取り専用 plan prompt をコピーします。

<!-- calibration-activation: plan-before-approval -->
```text
まだ activate しないでください。永続化 Calibration Session ID/path、prepared
Candidate revision と SHA-256、正確な configuration、現在の Active
configuration、全 checklist blocker、full self-check と Governance Simulation、
Reviewer/Owner confirmation の revision/digest を表示してください。同じ rollback
transaction が置換する Active/Session path、現在の識別子、Active failure、
Active 置換後の Session failure、rollback failure の正確な復旧動作を示します。
各事実を Observed、Inferred、Unknown に分け、最後に「証拠が揃い、この正確な
Candidate identity について別の activation 承認段階へ進むか」だけを yes/no で
1 件質問してください。yes は activation の承認ではありません。file 変更、
commit、push、PR 作成・merge、release、Work Item close は禁止です。
```

PASS は両 confirmation record が prepared Candidate revision/digest と一致し、
configuration に 10 行の回答/evidence が含まれ、Unknown、STOP、stale stage、
不足 field が 0 件の状態です。runtime がこれらの条件を machine enforce し、
承認するかは人が review して判断します。それ以外は STOP し、該当 checklist
row へ戻ります。PASS 後だけ、次の限定承認を別にコピーします。

<!-- calibration-activation: bounded-approval -->
```text
直前に review した正確な Calibration Session ID、prepared Candidate revision、
SHA-256 digest、configuration の activation だけを承認します。activate 直前に
Candidate digest を再計算し、変更、confirmation 不一致、checklist blocker が
あれば STOP してください。導入済み Calibration Session transaction だけで
activate し、前後の Active/Session 識別子、両方に永続化された同一 Candidate
identity、validation 結果を表示して停止します。Active または Session の永続化に
失敗した場合は、両 path が transaction 開始時の正確な bytes または不存在へ
戻ったことを確認します。rollback 失敗なら STOP と `consistency unproved` を
報告し、repository owner に連絡して、弱い根拠で再試行しません。commit、push、
PR 作成・merge、release、Work Item close は禁止です。
```

期待する結果: Unknown を隠さない prepared/digest-bound Candidate と完全な
inventory。Active/Session は 2 file rollback transaction を使用します。これは
復旧保証であり、物理的な multi-file atomicity の主張ではありません。両記録が
同じ Candidate identity を持って初めて成功です。人物認証、enterprise compliance、
runtime sandbox の証明ではありません。

<!-- calibration-activation-atomicity: active-session-rollback-transaction,candidate-digest-bound -->

<!-- novice-stage: run-local-checks -->
## 10. Local check を実行する

readiness 順序は、導入済み target `ai-cockpit-quality` の後に
`check-ai-adoption-ready` を実行する順です。次の prompt だけをコピーします。

<!-- public-quality-target: ai-cockpit-quality -->
<!-- readiness-target-order: ai-cockpit-quality,check-ai-adoption-ready -->
```text
導入済み target ai-cockpit-quality、check-ai-adoption-ready の順で実行します。
Make integration が別途 review・導入済みなら通常の make entrypoint、それ以外は
Makefile.ai entrypoint を使います。active Contract が宣言した check だけを対象に
します。実行前に正確な 2 command を表示して平易に説明し、この段階について私の
承認を待ってください。承認後に進捗を表示し、実際の pass/fail/not-run を記録し、
失敗時は停止します。gate の弱体化、skip、名称変更、commit、push、PR、merge、
release は行わないでください。
```

目的: プロジェクト品質の後に adoption evidence を検証します。成功: 両方が成功し
Summary に実結果を記録。失敗: output を保存して STOP。同じ Work Item で根因を
修正し、skip しません。

<!-- novice-stage: complete-first-work-item -->
## 11. Configuration Work Item を完了する

エージェントは `configure_ai_cockpit` の Summary、`before_finish` checkpoint、
導入済み `ai-finish` target に現在の task を渡し、Contract/Summary archive を完了し、diff と verification
を示します。人がレビューしてから archive-evidence commit を承認します。commit
承認は push 承認ではありません。
active Contract/Summary を渡さない場合、導入済み `check-ai-status` target は
`Skipping status check (no active contract/summary provided)` と表示することが
あります。その場合も導入済み `check-ai-status-consistency` target で active state がない
ことを確認します。

```text
configure_ai_cockpit だけを finish し、各 acceptance と implementation/test
evidence を対応させ、before_finish と ai-finish 後に profile、guard、quality
commands、CI、archive evidence の diff を平易に示してください。commit 判断を待ち、
push/PR はしないでください。
```

diff レビュー後に別途コピーします。

```text
レビュー済み configure_ai_cockpit archive bundle だけの local commit を 1 件
承認します。commit ID と clean worktree evidence を示して停止。push、PR、
merge、branch 削除、closure は禁止です。
```

PASS: レビュー済み configuration commit が 1 件で、worktree が clean。
STOP: 未レビュー file または check failure。リポジトリ担当者へ連絡します。

<!-- novice-stage: review-pr-and-hosted-ci -->
## 12. PR と hosted CI をレビューする

別の push 承認時にコピーします。

```text
configure_ai_cockpit branch だけを push し、証明済み default branch 向け PR を
準備してください。source branch を保持し、auto-merge/provider 自動削除を無効にし、
PR link、Head SHA、required hosted jobs を示して停止。merge/closure は禁止です。
```

PASS: base/Head SHA、PR link、全 required jobs が表示されます。STOP: push rejection、
wrong base/SHA、required job missing/skipped。リポジトリまたは CI 担当者へ連絡します。

PR は発見済み
default branch を対象にし、closure 用に source branch を残します。変更ファイル、
scope、Summary claim、required Job、Head SHA、hosted log を確認します。local
success は hosted success ではありません。

人のレビューと required hosted checks が通った場合だけ、人が手動 merge します。auto merge と provider の branch 自動削除は使いません。

GitHub の **Files changed** で diff、**Conversation** で reviewer decision、
**Checks** で required Job/log を確認し、PR の Head SHA と evidence commit を一致させます。

```text
configuration PR を読み取り専用で説明し、全 file を Contract scope/Summary に対応、
required GitHub Job の最終 state/Head SHA を列挙し、failure/skip を隠さず human merge
用 PASS/STOP を示してください。merge/branch 削除は禁止です。
```

<!-- novice-stage: merge-and-close -->
## 13. Merge 後に lifecycle を閉じる

merge 後、導入済み `ai-close-work-item` target で `configure_ai_cockpit` を
閉じる操作を別途承認します。closure は archive
evidence と PR ownership、fast-forward-only base sync、remote/local work branch
削除、clean worktree、local base と remote base の一致を検証します。1 件でも失敗したら closed ではありません。

<!-- lifecycle-approval: configuration-closure-plan -->
**A. 読み取り専用レビュー:**

```text
人が configure_ai_cockpit PR を merge 済みです。PR/archive ownership、merged
commit、正確な closure command、対象 branch、全 validation を示してください。
変更せず、判断を待って停止してください。
```

PASS: PR/archive/commit/branch/plan が一致。STOP: 不一致の evidence をリポジトリ
担当者へ渡します。

<!-- lifecycle-approval: configuration-closure-execute -->
**B. Closure だけを承認:**

```text
レビュー済み plan に従い configure_ai_cockpit の lifecycle closure だけを承認します。
ai-close-work-item を実行し、remote/local configuration branch 削除、clean worktree、
fast-forward-only 同期、local default と remote の一致を順番に示して停止。
失敗時は closed と報告せず、local/remote branch の実状態と残存証拠を示します。
branch が既に存在しない場合は merge 済み PR Head SHA と base の証拠から復旧する
計画を提示し、担当者へ連絡します。新 Work Item は開始しません。
```


<!-- novice-stage: recover-from-a-stop -->
## 14. 停止から復旧する

| 停止理由 | 安全な対応 |
| --- | --- |
| dirty worktree | 全ユーザー変更を識別・保持し、先に完了するか別 worktree を使う。 |
| initial commit なし | owner に initial commit の作成とレビューを依頼する。 |
| tool 不足 | Step 1 で特定した repository/build 管理者へ連絡し、review 済みの導入方法を取得してから Step 1 の読み取り専用調査を再実行する。 |
| default remote/branch 不明 | provider と remote HEAD を確認し、推測しない。 |
| active Work Item あり | finish/close または明示 resume。競合する active item を作らない。 |
| managed file conflict | 差分を説明し adopter content を保持して計画を修正する。 |
| Calibration Unknown | evidence を集めるか owner を割り当て、activate しない。 |
| local/hosted failure | log を保持し根因を修正して同じ check を再実行する。 |
| merge 後 closure failure | closed と報告しない。local/remote branch の実状態と証拠を確認し、branch が既にない場合は担当者承認後に merge 済み PR Head SHA から復旧する。 |

<!-- japanese-uninstall: entry -->
## 15. AI Cockpit を無効化またはアンインストールする

この手順は導入後に使います。ファイルを自分で探して削除しないでください。
通常は証拠を残す `preserve-evidence` を選びます。`disable` は実行を止めるだけで
ファイルを削除しません。`purge` は別の破壊的操作であり、通常の
アンインストール承認には含まれません。

<!-- japanese-uninstall: version-neutral -->
特定 version のコマンドをコピーせず、対象プロジェクトに**現在導入されている**
AI Cockpit の entrypoint と capability を毎回確認します。以下の prompt を上から
一つずつコピーしてください。各段階の承認は次の段階を許可しません。

<!-- japanese-uninstall: read-only-facts -->
### 15.1 削除前の事実を読み取り専用で確認する

目的: 何が AI Cockpit 管理、プロジェクト所有、変更済み、所有者不明かを分けます。

ここで確認するのは、現在の導入版、作業中の変更、各ファイルの所有者、導入時からの
ずれ、残す証拠の五分類です。

```text
AI Cockpit を無効化またはアンインストールしたいです。まだ何も変更・削除せず、
対象 repository、現在の installed release、clean/dirty 状態、active Work Item、
Runtime files、Managed Regions、project-owned files、変更済み files、unknown
ownership、drift、保持すべき Bootstrap Evidence、Archive、Human Decisions、
Project Policy、Complexity Baseline、Audit Evidence を読み取り専用で列挙してください。
各項目に observed evidence、PASS/STOP、不足時の owner を付け、推測しないでください。
内部 Python 関数を公開コマンドの代わりに実行しないでください。
```

PASS: 対象と ownership が証拠で確定し、変更済み・Unknown・drift がありません。
STOP: dirty、active Work Item、変更済み、Unknown、drift のいずれかがあります。
停止時は repository owner と該当ファイル owner が事実を確定するまで削除しません。

導入済み Runtime には読み取り専用の `ai-cockpit-uninstall-facts` entrypoint が
あります。エージェントにこの入口を使わせ、対象 repository、今回だけの
`sessionId`、出力先を先に表示させてください。出力は導入時 Manifest と現在の
filesystem を照合し、repository identity、installation ID、削除候補、保持対象を
決定します。absolute path、`..`、重複、symlink、変更済み file、Unknown ownership、
壊れた導入証拠は `blocked` です。手作り JSON や推測で 15.3 へ進みません。

<!-- japanese-uninstall: mode-choice -->
### 15.2 三つの mode から一つだけ選ぶ

```text
読み取り専用の結果だけを使い、disable、preserve-evidence、purge の違いを初心者向けに
説明してください。各 mode について、削除される候補、保持される証拠、戻し方、
不可逆な影響、追加確認、現在の実装で実行可能かを示してください。通常は
preserve-evidence を推奨し、私に一つだけ選ばせてください。まだ proposal の生成も
file 変更も行わないでください。
```

PASS: 一つの mode と理由が明確です。STOP: mode が曖昧、purge の影響が不明、
または disable が削除として説明されています。判断 owner は repository owner です。

`disable` を選んだ場合は uninstall proposal へ進みません。uninstall proposal は
`disable` を拒否し、`ai-cockpit-disable` を使うよう案内します。この別入口は結果
JSON を作りますが、canonical installed state を直接更新しません。repository owner
が state input、result output、canonical state への反映と再有効化を実装証拠で
示せない場合は STOP します。

<!-- japanese-uninstall: proposal-runtime-zero-write -->
### 15.3 Runtime を削除しない proposal だけを作る

15.1 の facts が `ready` の場合だけ、導入済み
`ai-cockpit-uninstall-propose` を使います。これは候補を JSON にまとめ、指定した
出力先に proposal JSON を一つ書きます。Runtime や管理対象 file は変更・削除
しません。初心者はコマンドを手入力せず、次をコピーします。

| 日本語表示 | 内部名 | 確認する内容 |
| --- | --- | --- |
| 確認番号 | `sessionId` | 今回だけの識別子 |
| Repository | `repositoryIdentity` / `installationId` | 同じ導入先か |
| 削除候補 | `deletionList` | Runtime 候補だけか |
| 保持 path | `preservePaths` | project、shared、generated、historical |
| 残す証拠 | `preserveEvidence` | Archive、判断、policy、audit の分類 |
| 証拠の退避 | `evidenceExport` | 必須か、完了したか |
| 別プロセス実行 | `detachedUninstaller` | 公開実装が存在するか |
| 完了記録 | `receipt` | 実行後に必須か |
| 正確な確認値 | `proposalDigest` | proposal 全体の SHA-256 binding |

```text
preserve-evidence について、導入済み ai-cockpit-uninstall-propose entrypoint を
使う計画を示してください。15.1 で生成した facts、選択 mode、proposal JSON の
出力先を表示し、上表の日本語名で内容を説明してください。実行前に
proposal JSON 一件の作成だけを承認する yes/no 質問をしてください。承認後は
生成結果、終了 code 0、state=needs_human_confirmation、writes が空であることを
表示して停止してください。proposalDigest も省略せず表示してください。exit 2
または state=blocked は STOP です。Runtime、Managed Regions、証拠 file は
変更・削除しないでください。
```

PASS: proposal の `writes` が空で、対象・保持証拠・receipt 要求が表示されます。
STOP: proposal が blocked、削除を始めた、または drift/ownership を無視しています。
停止時は repository owner が facts を修正し、15.1 から再確認します。

<!-- japanese-uninstall: preserve-evidence-default -->
### 15.4 保持内容と削除候補を一行ずつレビューする

```text
proposal を一行ずつ案内してください。Bootstrap Evidence、Archive、Human Decisions、
Project Policy、Complexity Baseline、Audit Evidence、project-owned files が保持され、
modified、unknown-owned、drifted files が deletionList にないことを確認します。
Runtime と Managed Regions は別に示し、各行へ evidence、PASS/STOP、owner を付けます。
不一致が一件でもあれば STOP し、proposal を変更・確認・実行しないでください。
```

PASS: 保持と削除候補が完全に分離されています。STOP: 証拠、project-owned、
変更済み、drift、Unknown の項目が削除候補です。担当は repository/audit owner です。

<!-- japanese-uninstall: bounded-confirmation -->
### 15.5 正確な proposal だけを確認する

```text
15.3 で保存した proposal JSON の repository identity、installation ID、session ID、
mode、正確な deletionList、preservePaths、receipt path、proposalDigest を
再表示してください。proposal の一項目でも変われば digest が無効になることを
説明し、一つでも変化・不足・Unknown があれば STOP してください。すべて一致する
場合だけ、表示した proposalDigest と完全に同じ値を削除実行の確認値として使うか
yes/no で一件質問してください。単なる「はい」や古い digest を実行承認に
置き換えないでください。
```

PASS: 同じ proposal identity が再確認されます。STOP: stale、export 未完了、
公開 executor 不在、または確認範囲が曖昧です。担当は repository owner です。

<!-- japanese-uninstall: detached-execution -->
### 15.6 Detached executor の実装境界を確認する

導入済み Runtime の `ai-cockpit-uninstall-execute` は、実行前に executor と必要な
検証 module を system temporary directory へコピーし、repository 内の削除候補
から分離した子 process だけが実行します。内部 `execute_proposal` の直接呼び出しは
`detached_execution_required` で停止します。子 process は proposalDigest、
repository identity、installation ID、現在の facts、receipt replay、symlink を
再検証してから、一致した unchanged Runtime file だけを削除します。

```text
導入済み public detached executor の entrypoint、system temporary directory への
分離方法、proposalDigest、repository identity、installation ID、session ID、
exact deletionList、preservePaths、partial-failure receipt を読み取り専用で
説明してください。project runtime を import せず、drift、unknown ownership、
symlink、receipt replay を再確認し、15.5 で表示した proposalDigest をもう一度
示して削除実行を yes/no で一件だけ質問してください。承認後はその exact digest
だけを渡して実行し、追加対象を推測しないでください。
```

PASS: temporary directory から起動した公開 executor と同じ proposal の実行証拠が
あります。STOP: detached 分離なし、digest 不一致、drift/Unknown、symlink、
対象追加、receipt replay、または partial failure です。担当は repository/release
owner です。

<!-- japanese-uninstall: receipt-verification -->
### 15.7 Receipt と Runtime Removal Verification を確認する

```text
実行後の最終 receipt を読み取り専用で表示し、session ID、detachedExecution、
実際に removed/preserved/missing/failed となった各 path、
runtimeRemovalVerified、残存 Runtime、Managed Regions、project-owned files、
Git status を proposal と照合してください。一致した項目だけ PASS とし、
不明・未確認・partial を completed と報告しないでください。
```

PASS: receipt と実 filesystem が一致し、Runtime removal が確認済みです。
STOP: receipt 不在、不一致、partial、証拠消失、または残存 Runtime があります。
停止時は実状態を保存し、repository/audit owner へ渡します。

<!-- japanese-uninstall: stop-recovery -->
### 15.8 STOP から再開する

```text
最後に PASS した段階、失敗した段階、proposal/session/digest、実 filesystem、
保持済み evidence、変更済み/unknown-owned/drifted path、未完了 action、owner を
一枚の recovery report にしてください。削除の再試行や弱い代替は行わず、必要な
証拠または実装修正後に同じ段階から再検証する計画だけを示してください。
```

PASS: 実状態と再開条件が証拠に結び付きます。STOP: 状態を推測する、receipt を
作り直す、手動削除を勧める、または証拠を消す場合です。

<!-- japanese-uninstall: purge-separate-confirmation -->
### 15.9 Purge は別の破壊的確認にする

`purge` は通常のアンインストール承認では実行できません。evidence export が完了し、
exact deletion list と不可逆な影響を人がレビューした後でも、project-owned files
と保護対象 audit evidence は除外します。

```text
purge proposal の evidence export receipt、exact deletion list、保持対象、
project-owned/audit 除外、不可逆な影響、復旧不能な項目を再表示してください。
通常の uninstall confirmation が purge を許可しないことを明記し、すべて確認済み
の場合だけ purge 専用の破壊的承認を yes/no で一件質問してください。
preserve-evidence executor は purge を実行しないため、purge 専用 executor が
未実装・未検証なら質問せず STOP してください。
```

PASS: 独立した purge 承認と公開 executor の証拠があります。STOP: export 未完了、
対象不明、除外違反、通常承認の流用、または executor 不在です。

<!-- novice-stage: confirm-installation-success -->
## 16. 最終成功チェック

- 選択した最上位の検証可能 release と fetch base が記録済み
- adoption/configuration が別 Work Item・branch・review lifecycle
- 全 scaffold path と conflict を説明済み
- Calibration 10 段階と Unknown をレビュー済み
- quality command がプロジェクト内の根拠に基づき実結果を記録
- 正しい Head SHA の required jobs が成功
- 人がレビュー・merge
- closure が両 work branch を削除し base を同期
- Cockpit Status と archive evidence が一致
- platform/security/enterprise 制限が明示

1 項目でも満たさなければ、現在の停止段階を説明し、導入成功とは報告しません。

## 参照

- [Standard Adoption Guide](standard-adoption-guide.ja.md)
- [Calibration Session](../reference/calibration-session.ja.md)
- [Adopter Configuration](adopter-configuration.ja.md)
- [Security and Release Verification](security-release-verification.ja.md)
- [Documentation Architecture](../reference/documentation-architecture.ja.md)
- [Upgrade](../reference/upgrade.ja.md)
- [Installed lifecycle（現在の proposal / executor 実装境界）](../reference/installed-lifecycle.md)
- [Capability Truth Matrix（現在実装済みか）](../reference/capability-truth-matrix.md)
- [日本語能力評価（release blocker）](../reference/japanese-capability-assessment.md)
