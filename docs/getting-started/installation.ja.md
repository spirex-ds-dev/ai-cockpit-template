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

これは英語版の要約ではなく、完全な日本語手順です。プログラミング経験は不要です。AI コーディングエージェントは調査と準備を行えますが、判断するのは常に人です。Governance Runtime の配置、プロジェクト固有の Calibration、最初の PR、ホステッド CI、マージ、ブランチクリーンアップは別々の段階です。

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

<!-- novice-stage: before-you-start -->
## 1. 始める前

必要なものは、対象プロジェクト、対象フォルダーを読める AI コーディングエージェント、Git、Python 3.10 以上、GNU Make、既存の Git commit 1 件以上、およびブランチと PR を作成する権限です。AI Cockpit テンプレートリポジトリへ誤って導入しないでください。失えないローカルデータは先にバックアップします。

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

```text
このプロジェクトへ AI Cockpit を導入したいです。最初は読み取り専用で調査してください。
明示的に検証済み private mirror を私が指定しない限り、正規 public source
https://github.com/spirex-ds-dev/ai-cockpit-template.git と metadata
https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/main/release.json
を使用してください。固定 tag を解決し、tag target、source commit、installer
digest、archive asset、SHA-256 evidence を報告し、不足・不一致で停止してください。
作成、編集、削除、commit、push、PR 作成・マージ、公開は禁止です。
関係のないユーザー変更をすべて保持してください。

プログラミング未経験者にも分かる言葉で調査・説明してください。
1. repository root、現在のブランチ、worktree の状態、initial commit の有無
2. remote HEAD が示す default remote/default branch と fetch 後の最新 commit
   （origin/main と仮定しない）
3. Python 3.10+、Git、GNU Make、curl の有無
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

現在の interactive Wizard で人が選ぶのは New Adoption、Upgrade、Dry Run の
mode だけです。stack と base/branch は検出され、他は fixed default または
CLI/environment control であり追加画面ではありません。

| 種類 | 項目 | 通常の動作 |
| --- | --- | --- |
| 選択可能 | Mode | 未導入なら **New Adoption**、既存導入の更新だけ **Upgrade**、書き込まず確認するなら **Dry Run**。 |
| 起動時の証拠 | Source | 初心者向け経路は公開済み固定 release を使います。local clone/private mirror は明示的な非公開 trust path です。 |
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

通常は New Adoption、正規の固定 public release、検出 stack（不確実なら
`generic`）、専用 adoption branch、Make integration なし、既存 glossary 保持、optional examples なし、
interactive review です。既存ファイルや組織ルールと衝突する場合は担当者へ確認します。

保守専用は `--upgrade` と `--upgrade-with-active` です。`--dry-run` は読み取り専用です。`AI_COCKPIT_TEMPLATE_REF` は明示 ref を指定し、`AI_COCKPIT_TEMPLATE_SHA256` は追加 assertion にすぎず、公開メタデータを置き換えません。

モバイル・Java プロジェクトは同じ言語の例を先に開きます:
[iOS](examples/ios.ja.md)、[Android](examples/android.ja.md)、
[Java](examples/java.ja.md)。

<!-- novice-stage: review-installation-plan -->
## 6. 導入計画をレビューする

```text
書き込まずに最終導入計画を示してください。固定 release と trust evidence、
fetch 後の base commit、新ブランチ、stack、全 installer option、
作成・変更・保持する全ファイル、競合、rollback、書き込み後チェックを含め、
各選択がこのプロジェクトに合う理由を説明してください。不明は Unknown としてください。
最後は scaffold の書き込みと検証だけを許可する yes/no 質問 1 件にしてください。
commit、push、PR、merge、release、削除、Calibration activation を求めないでください。
```

期待する結果: 正確な計画と限定された確認質問です。moving branch、default
branch の推測、隠れた競合、後続権限の一括要求があれば拒否します。

<!-- novice-stage: approve-scaffold-write -->
## 7. Scaffold 書き込みだけを承認する

計画が正しい場合、記載された install transaction と検証だけを許可します。installer は marker/競合を先に検証し、default base を発見・fetch し、adoption branch を作り、managed files を書きます。途中失敗時は部分導入を rollback します。

期待する結果: 専用 adoption branch と検証レポート。commit、push、PR、merge、release はありません。

承認前に対象 folder、clean worktree、fixed release evidence、fetched default
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
導入済み scaffold を読み取り専用で、(1) agent entrypoint、(2) glossary/policy/
guard/trust/profile、(3) adoption Contract/Summary/start receipt、(4) scripts/Make、
(5) Cockpit Status/evidence、(6) 既存 CI と後続 configuration gap、
(7) optional examples の順に確認してください。expected/actual path、状態、平易な
目的、validation、conflict recovery を表にし、missing/unplanned/invalid/conflict
で STOP。finish、commit、push、calibration はしないでください。
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

source repository の `templates/` と template supply-chain evidence は adopter
payload ではありません。Scaffold 作成だけでは Calibration、project quality、
CI、platform toolchain、production readiness を証明しません。

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

**C. Push と PR 準備を別承認:**

```text
adopt_ai_cockpit branch だけを push し、証明済み default branch 向け PR を準備する
ことを承認します。source branch を保持し、auto-merge/provider 自動削除を無効にし、
PR link、Head SHA、required hosted checks を示して停止。merge/closure は禁止です。
```

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
失敗時は branch/evidence を保持しリポジトリ担当者へ連絡してください。
configuration は開始しません。
```

期待する結果: adoption PR が human-merged、`adopt_ai_cockpit` が closed、
remote/local branch が削除され、local default branch が remote と一致します。

<!-- novice-stage: complete-calibration -->
## 9. Calibration の 10 段階をすべて完了する

adoption PR の merge と lifecycle closure を確認した後だけ、別の
`configure_ai_cockpit` Work Item を作ります。エージェントは
`make cockpit-doctor` と `make cockpit-calibrate` を実行し、導入済みの
`make cockpit-calibrate-session ARGS="..."` で再開可能な Session を進めます。
`make cockpit-calibration-wizard` は template maintenance 専用で adopter には
導入されません。初心者は下記 prompt を使い、Session command を手入力しません。
Candidate activation 前に Reviewer と Owner の別々の確認を待ちます。

回答形式は **yes/no**、正しい値を示す **alternative input**、証拠不足で readiness
をブロックする **unknown**、理由必須の **not applicable** の 4 種類です。

```text
同期済み default branch から configure_ai_cockpit を開始し、Calibration 10 段階を
順番に案内してください。各段階で、平易な質問、確認 files、observed evidence、
inference、Unknown、回答 type/value、Candidate 変更 file、PASS/STOP、reviewer を
表示します。yes/no、alternative_input、unknown、理由付き not_applicable だけを
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
| 段階 | コピーする依頼と根拠の例 | 続行できる状態（PASS） | 停止条件と連絡先（STOP） |
| --- | --- | --- | --- |
| 1 リポジトリの役割 | 「release/deploy ファイルから、アプリ、ライブラリ、複数構成のリポジトリ、テンプレート等のどれかを説明し、公開担当者を示してください。まだ回答を記録しません。」 | 役割と公開担当者を示すファイルがあり、説明を理解できる。 | 役割または担当者が不明。リポジトリ担当者へ連絡。 |
| 2 言語と stack | 「設定ファイル、言語版、build/package tool と preset が出発点にすぎない理由、代案を示してください。」`pom.xml` は JDK 導入済みの証明ではありません。 | 版と preset がプロジェクト内の根拠に一致する。 | 混在・特殊構成。platform 担当者へ連絡。 |
| 3 ソース範囲 | 「保守対象ソースと vendor/generated/cache/build を分け、全包含・除外理由を説明してください。」 | 全パスに担当者と理由がある。 | 保守コードを誤って除外する恐れ。module 担当者へ連絡。 |
| 4 テスト範囲 | 「unit、integration、UI/device、fixture、test-generated と必要環境を分けてください。」 | テスト種類と必要環境を画面上で区別できる。 | 種類または環境が不明。test/platform 担当者へ連絡。 |
| 5 生成物 | 「生成パス、generator、正本、再生成方法、直接編集ルールを示してください。」 | generator と差分確認ルールがファイルで確認できる。 | generator 不明。build 担当者へ連絡。 |
| 6 重要パス | 「security、release、migration、payment、identity、signing、deploy、プロジェクト固有の高リスクパスと reviewer を示してください。」 | 全重要パスに人の reviewer がいる。 | 担当者不足。security/release 担当者へ連絡。 |
| 7 品質コマンド | 「repo/CI の根拠から正確な command をコピーし、前提、目的、成功表示、失敗対応を説明してください。」 | 全 command に出典と期待表示がある。 | command の創作または前提不足。build/CI 担当者へ連絡。 |
| 8 レビュー要件 | 「CODEOWNERS、branch protection、required hosted checks、agent が承認できない操作を示してください。」 | 人の担当者と required checks が明確。 | provider の根拠を確認できない。repository 管理者へ連絡。 |
| 9 リスクと不明点 | 「全未解決事項、影響、担当者、復旧を示し、Unknown を N/A にしないでください。」 | 続行を妨げる Unknown がない。 | 1 件でも blocking Unknown。記載担当者へ連絡。 |
| 10 導入準備 | 「10 件の回答、設定案の差分、一覧、検査結果、残る制限、Reviewer/Owner の判断を示し、まだ有効化しないでください。」 | 全体検査が成功し、2 人が別々に確認している。 | 根拠の欠落・古さ・却下。該当段階へ戻る。 |

期待する結果: Unknown を隠さない Candidate と inventory。activation 失敗時は旧
Active configuration を保持します。enterprise compliance や runtime sandbox の証明ではありません。

<!-- novice-stage: run-local-checks -->
## 10. Local check を実行する

```text
active Contract が宣言した local check だけを実行してください。
各 check を平易に説明し、進捗を表示し、実際の pass/fail/not-run を記録し、
失敗時は停止してください。gate の弱体化、skip、名称変更は禁止です。
commit、push、PR、merge、release は行わないでください。
```

英語 authoritative document が固定する readiness 順序は
`make ai-cockpit-quality` の後に `make check-ai-adoption-ready` です。
導入済みの同じ入口を対象プロジェクトで実行し、結果を説明させます。

agent が実行する順序:

<!-- public-quality-target: ai-cockpit-quality -->
```text
make ai-cockpit-quality
make check-ai-adoption-ready
```

目的: プロジェクト品質の後に adoption evidence を検証します。成功: 両方が成功し
Summary に実結果を記録。失敗: output を保存して STOP。同じ Work Item で根因を
修正し、skip しません。

<!-- novice-stage: complete-first-work-item -->
## 11. Configuration Work Item を完了する

エージェントは `configure_ai_cockpit` の Summary、`before_finish` checkpoint、
`make ai-finish TASK=<task>`、Contract/Summary archive を完了し、diff と verification
を示します。人がレビューしてから archive-evidence commit を承認します。commit
承認は push 承認ではありません。
active Contract/Summary を渡さない場合、`make check-ai-status` は
`Skipping status check (no active contract/summary provided)` と表示することが
あります。その場合も `make check-ai-status-consistency` で active state がない
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

merge 後、`make ai-close-work-item TASK=configure_ai_cockpit` を別途承認します。closure は archive
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
失敗時は branch/evidence を保持し担当者へ連絡。新 Work Item は開始しません。
```


<!-- novice-stage: recover-from-a-stop -->
## 14. 停止から復旧する

| 停止理由 | 安全な対応 |
| --- | --- |
| dirty worktree | 全ユーザー変更を識別・保持し、先に完了するか別 worktree を使う。 |
| initial commit なし | owner に initial commit の作成とレビューを依頼する。 |
| tool 不足 | 組織承認済み方法で導入し、読み取り専用調査を再実行する。 |
| default remote/branch 不明 | provider と remote HEAD を確認し、推測しない。 |
| active Work Item あり | finish/close または明示 resume。競合する active item を作らない。 |
| managed file conflict | 差分を説明し adopter content を保持して計画を修正する。 |
| Calibration Unknown | evidence を集めるか owner を割り当て、activate しない。 |
| local/hosted failure | log を保持し根因を修正して同じ check を再実行する。 |
| merge 後 closure failure | branch を保持し lifecycle state を修正する。完了報告しない。 |

<!-- novice-stage: confirm-installation-success -->
## 15. 最終成功チェック

- 固定 release と fetch base が記録済み
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
- [Calibration Session](../reference/calibration-session.md)
- [Adopter Configuration](adopter-configuration.md)
- [Security and Release Verification](security-release-verification.ja.md)
- [Documentation Architecture](../reference/documentation-architecture.md)
- [Upgrade（英語の authoritative version）](../reference/upgrade.md)
