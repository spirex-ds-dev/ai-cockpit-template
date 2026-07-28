---
author: Ray
title: "インストール"
description: AI Cockpit を既存リポジトリへ導入するための日本語ガイド。
keywords:
  - ai-cockpit
  - installation
  - quick-start
---

# インストール

現在の能力と計画中の能力の境界は [Capability Truth Matrix](../reference/capability-truth-matrix.md) で確認できます。Runtime の導入だけでは校正は完了しません。現在の `configure_ai_cockpit` は Project Profile の提案を生成・検証し、中断・再開できる 10 Stage セッションと Candidate 有効化も実装済みですが、導入先での実行と人による確認が必要です。

AI Cockpit は、既存リポジトリへ公開済みリリースを導入します。このページは日本語利用者が Adoption、校正、PR、closure、CI、upgrade まで完了できる操作手順です。[英語版](installation.md)は対応する事実確認用であり、主経路の実行に必須ではありません。

判断対象に応じて、次の三層の日本語ガイドを使用してください。

- [30 秒で開始](30-second-start.ja.md): Wizard の最短経路と、その経路が行うこと・行わないこと。
- [標準導入ガイド](standard-adoption-guide.ja.md): 校正、Work Item、CI、人による承認、対象プロジェクト適合。
- [セキュリティとリリース検証](security-release-verification.ja.md): リリースメタデータ、digest、provenance、SBOM、trust root、mirror、企業統制境界。

## エントリポイントを選ぶ

remote から対話式に導入する場合は、[30 秒で開始](30-second-start.ja.md)の固定 tag download と interactive command を使います。`./install.sh --interactive` を直接実行するのは、固定 release の local template checkout がある場合だけです。Installation Wizard では New Adoption、Upgrade、Dry Run を選び、完全な計画を確認するまで対象リポジトリへ書き込みません。明示的な確認後も commit、push、PR、merge は行いません。自動化では既存の明示的な CLI オプションを使い、非 TTY の引数なし実行は待機せず fail closed になります。

インストール後の校正は `make cockpit-calibration-wizard` で開始します。10 段階の Session を保存し、Pause / Resume、Back、stale 再検証を行います。Unknown は確認を阻止し、Not Applicable には理由が必要です。Candidate 有効化には Reviewer と Owner の別々の確認が必要です。永続 Session schema は現在 `language: ja` を記録しますが、これは表示文字列がすべて日本語化済みという主張ではありません。

### 固定 release の installer を取得する

公開導入では、公開 `release.json` から tag を解決し、その tag の installer だけを実行します。次の copy-ready な既定値は正規 public repository を指します。private repository や mirror では推測した URL を使わず、local clone または明示的な source を使用します。

<!-- command-evidence: adopter_required -->
```sh
STACK="${STACK:-generic}"
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "${RAW_BASE}/main/release.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["releaseTag"])')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "${RAW_BASE}/${RELEASE_TAG}/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" \
  sh "$INSTALLER" --stack "$STACK" --update-makefile --create-adoption
ADOPTION_BASE="$(git rev-parse HEAD)"
```

`STACK` は `generic`、`python`、`go`、`rust`、`typescript`、`java`、`android`、`kotlin`、`flutter`、`swift`、`ruby`、`php`、`csharp` から選びます。実際の module、variant、SDK/JDK、formatter、test、build plugin が未確認なら `generic` を選び、Project Calibration で確定します。`swift` は Swift Package Manager が確認できる場合の出発点であり、Xcode workspace/project と CocoaPods の証明にはなりません。

## 導入の流れ

1. **事前確認:** Git の作業ツリーが clean で、初回コミット、Python 3.10 以上、GNU Make が利用できることを確認します。
2. **インストール:** 対象プロジェクトに合う stack preset を選びます。導入先のリモート既定ブランチから作業ブランチを作成し、テンプレートの公開 release tag `v0.5.42` を使います。
3. **Adoption:** 生成された `adopt_ai_cockpit` Work Item を finish し、status を確認します。
4. **キャリブレーション:** Project Profile と Guard の提案をレビューし、プロジェクト固有の品質コマンドを設定します。
5. **検証:** `make check-ai-adoption-ready`、`make ai-cockpit-quality`、`make check-ai-status-consistency` を実行します。

## 事前確認

<!-- command-evidence: adopter_required -->
```sh
git status --short
git rev-parse --is-inside-work-tree
git rev-list --count HEAD
python3 --version
command -v make
```

作業ツリーが汚れている場合や初回コミットがない場合、インストーラーは fail closed します。まず原因を解消してから再実行してください。

## 導入後

<!-- command-evidence: adopter_required -->
```sh
make ai-onboard
make check-ai-adoption-ready
make ai-cockpit-quality
make check-ai-status-consistency
```

上のコマンドはコピー直後の診断用です。導入は実行系の配置であり、Project Profile、Guard、品質コマンド、CI の本番適合は、別の `configure_ai_cockpit` Work Item で人が確認します。

## Adoption Work Item を完了する

installer が生成した `adopt_ai_cockpit` は、導入で変更した全ファイルを所有します。`ADOPTION_BASE` には導入前 commit を使用します。

<!-- command-evidence: adopter_required -->
```sh
make ai-finish TASK=adopt_ai_cockpit
make check-ai-status
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT="$ADOPTION_BASE"
```

これは自動公開スクリプトではありません。次の境界ごとに停止します。

1. local finish/archive 後に diff をレビューし、commit の承認を取得します。
2. commit 後、push のために別の承認を取得します。
3. PR を作成しますが、auto-merge と provider 側の source branch 自動削除は無効にします。
4. 人が PR を merge します。
5. merge 後、closure の承認を取得してから次を実行します。

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

closure は archive evidence、PR/branch ownership、base の fast-forward 同期、local/remote branch 削除、clean worktree、remote base との一致を検証します。失敗した場合は閉鎖済みと報告せず、原因を解消します。

## Project Calibration を別 Work Item で行う

Adoption PR の closure 後、設定専用 Work Item を開始します。Contract の変更範囲には、実際に変更する `.ai/project_profile*`、`.ai/guards/**`、`Makefile.ai.stack`、GitHub Actions または GitLab CI だけを明記します。skeleton unknown、acceptance、capability、execution decision、guideline を完成させてから `before_edit` checkpoint を記録します。

<!-- command-evidence: adopter_required -->
```sh
CONFIG_BASE="$(git rev-parse HEAD)"
make ai-start TASK=configure_ai_cockpit TITLE="Configure AI Cockpit for this project" MODE=code
make ai-onboard
# または個別に:
make cockpit-doctor
make cockpit-calibrate
```

`cockpit-doctor` は `target/ai_project_doctor_report.json` に read-only な事実を記録します。`cockpit-calibrate` は `.ai/project_profile.proposed.yaml` を生成しますが、Guard を変更せず、境界を承認しません。proposal、`blocking:` unknown、品質コマンド、Coverage、CI を人が確認し、承認済み `.ai/project_profile.yaml` を作成します。

<!-- command-evidence: adopter_required -->
```sh
make check-ai-project-profile
make check-ai-guard-calibration
make ai-cockpit-quality
make check-ai-adoption-ready
make ai-finish TASK=configure_ai_cockpit
git add .
git commit -m "configure AI Cockpit for this project"
make check-ai-pr AI_BASE_COMMIT="$CONFIG_BASE"
```

設定 PR でも commit、push、merge、`make ai-close-work-item TASK=configure_ai_cockpit` の前にそれぞれ承認を取得します。Unknown または stale な証拠が残る場合、readiness は fail closed です。Session は企業 security、sandbox、identity、compliance を保証しません。

## CI と導入準備を検証する

CI は full Git history を取得します。最初に L1 の `check-ai-pr` を安定させ、その後 L2 の公開品質入口 `ai-cockpit-quality` を別の required job として追加します。default branch や remote 名を `origin/main` と仮定せず、対象 provider の base branch から merge-base を求めます。

<!-- command-evidence: adopter_required -->
```sh
ADOPTER_REMOTE="${ADOPTER_REMOTE:?Contract に記録された remote を設定してください}"
ADOPTER_DEFAULT_BRANCH="${ADOPTER_DEFAULT_BRANCH:?Contract に記録された default branch を設定してください}"
make check-ai-pr AI_BASE_COMMIT="$(git merge-base HEAD "$ADOPTER_REMOTE/$ADOPTER_DEFAULT_BRANCH")"
make ai-cockpit-quality
make check-ai-adoption-ready
make check-ai-status-consistency
```

remote/default branch は installer が Contract に記録した実値を使用します。`check-ai-adoption-ready` は command の意味的な十分性を推測できないため、対象工程の formatter、test、build、Coverage、mobile variant を Hosted CI で実行し、その結果を人が確認します。

## Upgrade

upgrade は active Work Item がない clean repository で行います。`TARGET_VERSION` は installed `.ai/cockpit/version.json` より新しい published tag にします。active task 中の `--upgrade-with-active` は高リスク recovery override であり、通常経路では使用しません。

<!-- command-evidence: adopter_required -->
```sh
CURRENT_VERSION="${CURRENT_VERSION:?installed release tag を設定してください}"
TARGET_VERSION="${TARGET_VERSION:?より新しい published tag を設定してください}"
test "$TARGET_VERSION" != "$CURRENT_VERSION"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "${AI_COCKPIT_TEMPLATE_RAW_BASE:?raw-content base を設定してください}/$TARGET_VERSION/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REF="$TARGET_VERSION" \
  sh "$INSTALLER" --upgrade --stack "$STACK"
```

managed file は `.ai/cockpit/upgrade-backups/<timestamp>/` へ退避され、検証失敗時は自動 rollback されます。project-owned `.ai/glossary.md` は既定で保持され、`--replace-glossary` を明示した場合だけ backup 後に置換します。`--force` は backup なしで managed file を置換するため、通常 upgrade の代わりに使いません。

## Runtime と対象工程の境界

- Python 3.10 以上、Git、POSIX shell、GNU Make 互換動作が必要です。
- 対応 runtime/CI は Linux と macOS です。Native Windows shell は対象外で、WSL などの POSIX 環境を使います。
- Android の module/flavor/variant、JDK、unit/instrumented test は対象の Gradle Wrapper に合わせます。
- Xcode project/workspace と CocoaPods は Swift Package の Hosted fixture から推論できません。
- template fixture の成功は、対象工程の SDK、toolchain、branch policy、provider control の証拠ではありません。

設定と検証が完了した後、[最初の Work Item](first-work-item.ja.md) に進んでください。

Android の module / flavor / variant、JDK、unit test、instrumented test は導入先の Gradle Wrapper に合わせて校正します。Xcode project/workspace と CocoaPods は Swift Package の検証結果から推論できません。混在 monorepo は境界を確定するまで `generic` を選び、fixture の存在を外部ツールチェーン実行の証拠とみなさないでください。
