# Task Outcome: fix-shellcheck-apt-mirror-20260819

Status: `completed`
Human Status: `green`

## Outcome Summary
Task fix-shellcheck-apt-mirror-20260819 generated an evidence-derived outcome with status completed.

## Task Overview
Governed Work Item: fix-shellcheck-apt-mirror-20260819

## Delivered Changes
- .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json
- .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json
- .ai/cockpit/current_status.md
- .ai/work-items/starts/fix-shellcheck-apt-mirror-20260819.json
- .github/workflows/compatibility.yml
- tests/test_workflows.py
- .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json
- scripts/installer/legacy.py
- tests/test_installer.py
- Makefile
- tests/test_makefile.py
- .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.json
- .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.md
- .ai/cockpit/task_report.json
- .ai/cockpit/task_report.md
- docs/reference/capability-truth-matrix.json
- docs/reference/capability-truth-matrix.md
- docs/reference/japanese-capability-assessment.json
- docs/reference/japanese-capability-assessment.md
- docs/reference/pre-release-documentation-alignment.json
- docs/reference/pre-release-documentation-alignment.md

## Findings
None

## Risks
None

## Warnings
None

## Limitations
None

## Non-Risk Explanations
None

## Forbidden Claims
None

## Interventions
None

## Forced Stops
- verification
- verification
- verification

## Resolutions
- aiGuidelines failed before the retry.
- quality failed before the retry.
- aiSummary failed before the retry.

## Recurrence Prevention
None

## Avoided Impact
- If not detected, could have led to a stale completion claim.

## Residual Risks
- hosted_verification

## Human Decisions
None

## Evidence
- Contract
- Summary
- ShellCheck job definition
- workflow source regression test
- installer boundary and installed quality regression
- clean snapshot project-test shard regression
- verificationHistory[0] aiGuidelines failed
- verification[aiGuidelines] retry passed
- verificationHistory[1] quality failed
- verification[quality] retry passed
- verificationHistory[2] aiSummary failed
- verification[aiSummary] retry passed

## Implementation Approach
Status: `complete`
Customer summary (verified): 本次将兼容性检查从网络安装 ShellCheck 改为使用固定 Ubuntu 24.04 runner 已提供的 ShellCheck，并在实际检查前执行版本探测；同时将模板仓库专属的 reference-impact 证据限定为 source-only，并修复 clean snapshot 的 project-test shard 空 diff 收尾，避免干净提交在 quality 中被错误阻断。
Mechanism (verified): ShellCheck job 固定运行在 ubuntu-24.04；先执行 shellcheck --version，runner 未提供可用命令时立即失败，随后执行既有的 shellcheck install.sh。安装器在复制 .ai 树时跳过模板仓库专属的 reference-impact 记录；project-test shard 仅在存在实际 git diff 时调用 git apply；回归测试覆盖 workflow、fresh adopter 与 clean snapshot 边界。

Affected components
- Hosted compatibility ShellCheck lane: Only the runner image selection and tool bootstrap steps change; compatibility-gate dependency and ShellCheck policy remain unchanged. (verified)
- Workflow regression tests: The test rejects apt-get update/package installation and requires the version probe plus install.sh invocation. (verified)
- Adopter installer evidence boundary: Template repository reference-impact records are source-only repository evidence and are not copied into a fresh adopter; adopters can create their own records for their own targets. (verified)
- Isolated project-test shard preparation: A clean committed snapshot skips the git apply step when there is no tracked diff; non-empty tracked diffs continue to be applied before shard execution. (verified)

Design decisions
- Use the runner-provided ShellCheck instead of installing it through apt.: Hosted evidence shows the job repeatedly timed out at azure.archive.ubuntu.com before ShellCheck started, while the pinned runner image provides ShellCheck. (verified)
- Pin the ShellCheck lane to Ubuntu 24.04.: The tool availability assumption is kept stable at the workflow boundary instead of depending on a moving ubuntu-latest image. (verified)
- Do not distribute template repository reference-impact records to adopters.: Those records bind to template-local target paths; copying them into an adopter makes the adopter's full-repository reference-impact check fail when the target workflow is absent. (verified)
- Treat an empty tracked git diff as a valid isolated-shard input.: Hosted verification uses a clean committed snapshot; piping an empty diff to git apply returns 128 even though there are no changes to apply. (verified)

### Technical details
- Failure handling: shellcheck --version is a fail-closed availability probe; a missing or unusable executable stops the job before the analysis command. (verified)

### Evidence
- The workflow no longer depends on the failing apt mirror path.: .github/workflows/compatibility.yml#ShellCheck job definition (verified)
- The regression guard prevents reintroducing the network bootstrap and preserves the actual ShellCheck invocation.: tests/test_workflows.py#workflow source regression test (verified)
- Fresh adopters do not inherit template-local reference-impact records that point to absent workflow paths.: tests/test_installer.py#installer boundary and installed quality regression (verified)
- Clean committed snapshots no longer fail isolated project-test shard preparation because of an empty git diff.: tests/test_makefile.py#clean snapshot project-test shard regression (verified)

## Human Handoff
Locale: `en`

### What was completed
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json: Records the hosted CI failure evidence, scope, acceptance, and corrective boundaries.
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json: Records the evidence-bound implementation approach and verification handoff.
- Changed .ai/cockpit/current_status.md: Generated status projection for this governed Work Item.
- Changed .ai/work-items/starts/fix-shellcheck-apt-mirror-20260819.json: Generated lifecycle start evidence.
- Changed .github/workflows/compatibility.yml: Uses the pinned Ubuntu 24.04 runner's ShellCheck and removes the failing apt mirror bootstrap.
- Changed tests/test_workflows.py: Prevents reintroducing network-dependent ShellCheck installation while preserving the blocking invocation.
- Changed .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json: Binds the workflow change to the repository-local reference-impact analysis required by the PR gate.
- Changed scripts/installer/legacy.py: Prevents source-only template reference-impact records from being copied into adopters where their target workflow paths do not exist.
- Changed tests/test_installer.py: Verifies the installer pruning boundary and fresh-adopter quality behavior for source-only reference-impact evidence.
- Changed Makefile: Skips empty git-diff application in isolated project-test shards so clean committed snapshots remain executable.
- Changed tests/test_makefile.py: Prevents regression of the clean-snapshot project-test shard no-op boundary.
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.json: Mandatory Task Outcome evidence generated by ai-finish.
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.md: Mandatory Task Outcome evidence generated by ai-finish.
- Changed .ai/cockpit/task_report.json: Generated machine-readable Human Benefit Review Report.
- Changed .ai/cockpit/task_report.md: Generated human-readable Human Benefit Review Report.
- Changed docs/reference/capability-truth-matrix.json: Generated source-bound evidence during ai_finish; sha256 before=d474eee55a3a7c8448134e2ea87e1352c640fa9e4d184771c811ed3d2218108b, after=7eb7861a7db6ec64fa8ef4bdd723275deef1ad4744fd3ca2e12acd0870bdc58e.
- Changed docs/reference/capability-truth-matrix.md: Generated source-bound evidence during ai_finish; sha256 before=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f, after=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f.
- Changed docs/reference/japanese-capability-assessment.json: Generated source-bound evidence during ai_finish; sha256 before=20e2d1f3c55221f097211ecc29ad3d7f96bab24ea8b2bcbd1fdd7e9812269e55, after=20e2d1f3c55221f097211ecc29ad3d7f96bab24ea8b2bcbd1fdd7e9812269e55.
- Changed docs/reference/japanese-capability-assessment.md: Generated source-bound evidence during ai_finish; sha256 before=86bd31a5bd108126fc8f00f98ae41e2614d1a6dc54bbdb57b18114e69c36eb94, after=86bd31a5bd108126fc8f00f98ae41e2614d1a6dc54bbdb57b18114e69c36eb94.
- Changed docs/reference/pre-release-documentation-alignment.json: Generated source-bound evidence during ai_finish; sha256 before=061359b8c663129664dcaa3803a7e61e93217d9a761a21f200eb3a9620e700f0, after=97ff42091a0c811384865c7c45fd77804a922ce8d86eb7e66ef06870df5308a5.
- Changed docs/reference/pre-release-documentation-alignment.md: Generated source-bound evidence during ai_finish; sha256 before=8e81262f8d93910b53465e6d0427f33b6df49298de3439f31c4eab20643988e1, after=4ca6bdc4b669d7c63af929fc9094e6d0eb9643f85af306ac4e3688d7b2dd56ef.

### What passed
- sourceBoundEvidence: capability truth generated: docs/reference/capability-truth-matrix.json sha256 before=c35a4db246cd1f846d167245b43ff63b9756469bb9fee44d85000234624d5b4e, after=db93c0eb585d86b2588a57c22883b094c71d075b37100a4daf86f4899e59f2ea; docs/reference/capability-truth-matrix.md sha256 before=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f, after=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f capability truth matrix check passed: <PROJECT_ROOT>/docs/reference/capability-trut
- aiWorkItem: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_work_item.py .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json work item contract check passed: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json
- aiScope: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_scope.py .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json scope guard passed: 20 changed path(s) covered
- aiGuards: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_guards.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json [warning] restricted_write: .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json (.ai/**) - AI governance configuration. [warning] restricted_write: .github/workflows/compatibility.yml (.github/workflows/**) - CI workflow configuration. [warning] restricted_write: Makefile (Makefile) - Shared local and CI command entrypoint. guard ch
- aiCheckpoint: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_checkpoint.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json --stage "before_finish" # AI Work Item Checkpoint - Stage: `before_finish` - Work Item: `fix-shellcheck-apt-mirror-20260819` - Contract Hash: `070b05551e968861` - Mode: `code` - notCodable: `False` - Execution Decision: `continue` - Acceptance Count: `6` - Unknown Count: `0
- aiReviewPolicy: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_review_policy.py --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json review policy matched 10 path(s) [review] .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json [review] .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json [review] .ai/work-items/starts/fix-shellcheck-apt-mirror-20260819.json [review] .ai/cockpit/current_status.md [review] .ai/cockpit/task_report.json [review
- aiBacktrack: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_backtrack.py backtrack guard: no issues report: target/ai_backtrack_report.json
- aiCoverage: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_coverage_guard.py coverage guard: no issues report: target/ai_coverage_guard_report.json
- aiScenarioCoverage: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_scenario_coverage.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json [warning] missing_scenario_coverage: - scenario coverage is missing for medium/high risk report: target/ai_scenario_coverage_report.json
- aiGuidelines: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_guidelines.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json guidelines compliance check passed: 3 guideline(s) verified
- aiDiffOwnership: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_diff_ownership.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json ## Diff Ownership Preview - active_owned: `20`, ambiguous: `0`, approval_required: `0`, archived_owned: `0`, out_of_scope: `0`, unowned: `0` - [active_owned] `.ai/cockpit/current_status.md` — covered by Contract scope - [active_owned] `.ai/cockpit/task_report.json` — exact generated Human Benefit Report pair validates against active Task Outc
- quality: {"finishQualityRoute": {"command": "make ai-cockpit-quality GOVERNANCE_PROFILE=strict", "policy": {"domains": ["docs", "installer", "tests", "trust", "unknown", "workflow"], "level": "strict", "qualityRouting": {"reason": "high-risk strict paths require full quality: .github/workflows/compatibility.yml, scripts/installer/legacy.py", "requiredGroups": ["quality-full"], "target": "quality-full"}, "qualityTarget": "quality-full", "requiredGroups": ["quality-full"], "scope": "full", "stage": "task"}
- aiStatus: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_generate_status.py .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json cockpit status generated: <PROJECT_ROOT>/.ai/cockpit/current_status.md
- aiStatusCheck: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_status.py .ai/cockpit/current_status.md --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json cockpit status check passed: .ai/cockpit/current_status.md
- aiStatusConsistency: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_status_consistency.py ai status consistency check passed
- aiAgentRisk: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_agent_risk.py --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json --summary .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json agent risk check passed report: target/ai_agent_risk_report.json
- aiSummary: PYTHONDONTWRITEBYTECODE=1 <LOCAL_PATH> scripts/ai_check_summary.py .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json --contract .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json ai summary check passed: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json

### What was retained
None

### Risks
- hosted_verification: The workflow fix removes the observed apt mirror dependency, but PR #906 must be revalidated on hosted CI after this corrective change merges.

### Red reasons
None

### Human questions
- problemCount: 3
- blockedProblems: None
- resolvedProblems: aiGuidelines failed before the retry.; quality failed before the retry.; aiSummary failed before the retry.
- resolutionApproach: Re-ran aiGuidelines after the correction; the latest attempt passed.; Re-ran quality after the correction; the latest attempt passed.; Re-ran aiSummary after the correction; the latest attempt passed.
- avoidedRisks: If not detected, could have led to a stale completion claim.; If not detected, could have led to a stale completion claim.; If not detected, could have led to a stale completion claim.
- remainingRisks: The workflow fix removes the observed apt mirror dependency, but PR #906 must be revalidated on hosted CI after this corrective change merges.
- agentUnknowns: None
- humanConfirmations: None
- recurrenceLikelihood: unknown: no direct recurrence probability evidence was recorded.
- nextTime: Bind conversation locale and preserve evidence details before the next Work Item starts.
