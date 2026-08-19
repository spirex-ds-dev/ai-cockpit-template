# Task Outcome: fix-dependency-pin-quality-routing-20260819

Status: `completed`
Human Status: `green`

## Outcome Summary
Task fix-dependency-pin-quality-routing-20260819 generated an evidence-derived outcome with status completed.

## Task Overview
Governed Work Item: fix-dependency-pin-quality-routing-20260819

## Delivered Changes
- .ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.contract.json
- .ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.summary.json
- .ai/cockpit/current_status.md
- .ai/work-items/starts/fix-dependency-pin-quality-routing-20260819.json
- docs/reference/capability-truth-matrix.json
- docs/reference/japanese-capability-assessment.json
- docs/reference/japanese-capability-assessment.md
- docs/reference/pre-release-documentation-alignment.json
- docs/reference/pre-release-documentation-alignment.md
- scripts/ai_verification_policy.py
- scripts/determine_governance_profile.py
- scripts/ai_finish.py
- tests/test_verification_policy.py
- tests/test_governance_profile.py
- tests/test_core_gates.py
- .ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.outcome.json
- .ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.outcome.md
- .ai/cockpit/task_report.json
- .ai/cockpit/task_report.md
- docs/reference/capability-truth-matrix.md

## Findings
None

## Risks
None

## Warnings
None

## Limitations
None

## Non-Risk Explanations
- {"evidence": [{"source": ".ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.contract.json", "subject": "outOfScope and acceptance hosted-verification boundary"}, {"source": ".ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.summary.json", "subject": "knownGaps"}], "reason": "This corrective WI changes only local evidence-bound routing. Hosted verification remains an explicit acceptance requirement of the future dependency successor and is not being claimed here.", "sourceWarning": "Hosted CI behavior for the future dependency successor remains external evidence."}
- {"evidence": [{"source": ".ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.contract.json", "subject": "outOfScope cancellation and timeout boundary"}, {"source": ".ai/work-items/archive/2026/fix-dependency-pin-quality-routing-20260819.summary.json", "subject": "knownGaps"}], "reason": "This WI fixes quality routing only. Process-tree cancellation, hard timeout, and scratch worktree cleanup remain a separately scoped corrective WI and are not silently claimed as fixed.", "sourceWarning": "The cancellation/timeout process-tree cleanup is intentionally a separate follow-up Work Item."}

## Forbidden Claims
None

## Interventions
None

## Forced Stops
- verification
- verification
- verification
- verification

## Resolutions
- quality failed before the retry.
- quality failed before the retry.
- quality failed before the retry.
- quality failed before the retry.

## Recurrence Prevention
None

## Avoided Impact
- If not detected, could have led to a stale completion claim.

## Residual Risks
- scope

## Human Decisions
None

## Evidence
- Contract
- Summary
- Evidence-bound base/current routing receipt integration
- verificationHistory[0] quality failed
- verification[quality] retry passed
- verificationHistory[1] quality failed
- verificationHistory[2] quality failed
- verificationHistory[3] quality failed

## Implementation Approach
Status: `complete`
Customer summary (verified): 将严格质量路由绑定到 Work Item Contract 的 base/current 文件证据：只有非发布工作流中恰好一行从一个 40 位 action SHA 替换为另一个 40 位 SHA 时，才投影为 targeted strict；生成的生命周期记录不再作为风险路径重复升级。所有其他形状继续走完整 strict 质量检查。
Mechanism (verified): 路由器先读取 Contract baseCommit 对应的工作流文件和当前文件，使用精确的一行替换判定；Finish 与 governance profile 两条入口共享同一判定器。任务状态、报告和 Outcome 等生成投影只参与证据记录，不参与严格风险路径选择。

Affected components
- Strict quality routing: Exact immutable workflow pin updates use quality-strict-targeted with quality-fast only; unsafe or high-risk shapes remain quality-full. (verified)
- Governance profile receipt: Routing facts include the evidence-bound immutablePinChange classification without exposing file contents. (verified)
- Finish lifecycle: Generated lifecycle projections are excluded from quality risk paths and Finish binds the classifier to the Contract base. (verified)

Design decisions
- Fail closed for every shape other than one exact immutable SHA replacement.: A routing optimization must not lower proof requirements for action identity, mutable references, extra changes, or release/signing workflows. (verified)
- Use repository evidence rather than path names or self-declared intent.: The same rule must be trustworthy in both automatic profile selection and final Finish routing. (verified)

### Technical details
- Evidence binding: Both routing callers read the Contract baseCommit and current workflow bytes before accepting the targeted route; unavailable evidence produces an ineligible classification. (verified)
- Generated projection boundary: Lifecycle status, Outcome, start, and Human Benefit Report files remain auditable outputs but are excluded from strict quality risk-path selection. (verified)

### Evidence
- The routing implementation and its real-sample behavior are covered by the evidence-bound classifier, governance integration test, and Finish integration test.: tests/test_governance_profile.py#Evidence-bound base/current routing receipt integration (verified)

## Human Handoff
Locale: `en`

### What was completed
- Changed .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json: Defines the bounded evidence-bound routing correction and release-cleanliness boundary.
- Changed .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json: Records implementation, verification, and residual-risk evidence for this Work Item.
- Changed .ai/cockpit/current_status.md: Generated lifecycle projection refreshed by governed checks.
- Changed .ai/work-items/starts/fix-dependency-pin-quality-routing-20260819.json: Canonical Work Item start receipt.
- Changed docs/reference/capability-truth-matrix.json: Source-bound capability digests regenerated after routing script changes.
- Changed docs/reference/japanese-capability-assessment.json: Source-bound Japanese capability assessment regenerated after matrix refresh.
- Changed docs/reference/japanese-capability-assessment.md: Human-readable Japanese capability projection regenerated.
- Changed docs/reference/pre-release-documentation-alignment.json: Source-bound documentation alignment projection regenerated after evidence refresh.
- Changed docs/reference/pre-release-documentation-alignment.md: Human-readable documentation alignment projection regenerated.
- Changed scripts/ai_verification_policy.py: Adds fail-closed immutable workflow SHA diff classification and targeted strict routing.
- Changed scripts/determine_governance_profile.py: Binds routing to base/current evidence and excludes generated projections from risk paths.
- Changed scripts/ai_finish.py: Uses the same evidence-bound pin classifier and excludes task report projections.
- Changed tests/test_verification_policy.py: Covers immutable-pin eligibility and fail-closed boundaries.
- Changed tests/test_governance_profile.py: Covers generated-projection isolation and base/current routing receipt integration.
- Changed tests/test_core_gates.py: Covers Finish-side evidence binding, generated projection exclusions, and unavailable-evidence fail-closed behavior.
- Changed .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.outcome.json: Mandatory Task Outcome evidence generated by ai-finish.
- Changed .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.outcome.md: Mandatory Task Outcome evidence generated by ai-finish.
- Changed .ai/cockpit/task_report.json: Generated machine-readable Human Benefit Review Report.
- Changed .ai/cockpit/task_report.md: Generated human-readable Human Benefit Review Report.
- Changed docs/reference/capability-truth-matrix.md: Generated source-bound evidence during ai_finish; sha256 before=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f, after=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f.

### What passed
- sourceBoundEvidence: capability truth generated: docs/reference/capability-truth-matrix.json sha256 before=bf222c53edf780574f1dd13f33fd850a311189862fcbcc117964c3870a75ef88, after=f6550a47c7dfe7463f07a5ea492c8c29c23dfac484850ebd2b61e268b6bc2c87; docs/reference/capability-truth-matrix.md sha256 before=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f, after=560be79ad6925d5087d7e2a3860c41aa3bf48afe7019b3c663165f9d95cd485f capability truth matrix check passed: <PROJECT_ROOT>/docs/reference/capability-trut
- aiWorkItem: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_work_item.py .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json work item contract check passed: .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json
- aiScope: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_scope.py .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json scope guard passed: 19 changed path(s) covered
- aiGuards: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_guards.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json guard check completed: 0 warning(s) report: target/ai_guard_report.json
- aiCheckpoint: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_checkpoint.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json --stage "before_finish" # AI Work Item Checkpoint - Stage: `before_finish` - Work Item: `fix-dependency-pin-quality-routing-20260819` - Contract Hash: `58d695c06077c82f` - Mode: `code` - notCodable: `False` - Execution Decision: `continu
- aiReviewPolicy: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_review_policy.py --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json review policy matched 9 path(s) [review] .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json [review] .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.outcome.json [review] .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.outcome.md [review] .ai/work-items/
- aiBacktrack: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_backtrack.py backtrack guard: no issues report: target/ai_backtrack_report.json
- aiCoverage: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_coverage_guard.py coverage guard: no issues report: target/ai_coverage_guard_report.json
- aiScenarioCoverage: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_scenario_coverage.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json report: target/ai_scenario_coverage_report.json
- aiGuidelines: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_guidelines.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json guidelines compliance check passed: 4 guideline(s) verified
- aiDiffOwnership: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_diff_ownership.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json ## Diff Ownership Preview - active_owned: `19`, ambiguous: `0`, approval_required: `0`, archived_owned: `0`, out_of_scope: `0`, unowned: `0` - [active_owned] `.ai/cockpit/current_status.md` — covered by Contract scope - [active_owned] `.ai/cockpit/task_report.json` — exact generated Human Benefit Report pair valida
- quality: {"finishQualityRoute": {"command": "make ai-cockpit-quality GOVERNANCE_PROFILE=strict", "policy": {"domains": ["docs", "project_code", "tests"], "level": "strict", "qualityRouting": {"reason": "strict paths without a targeted routing rule require full quality: docs/reference/capability-truth-matrix.json, docs/reference/japanese-capability-assessment.json, docs/reference/japanese-capability-assessment.md, docs/reference/pre-release-documentation-alignment.json, docs/reference/pre-release-document
- aiStatus: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_generate_status.py .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json cockpit status generated: <PROJECT_ROOT>/.ai/cockpit/current_status.md
- aiStatusCheck: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_status.py .ai/cockpit/current_status.md --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json cockpit status check passed: .ai/cockpit/current_status.md
- aiStatusConsistency: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_status_consistency.py ai status consistency check passed
- aiAgentRisk: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_agent_risk.py --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json --summary .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json agent risk check passed report: target/ai_agent_risk_report.json
- aiSummary: PYTHONDONTWRITEBYTECODE=1 <PROJECT_ROOT>/.venv/bin/python scripts/ai_check_summary.py .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json --contract .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.contract.json ai summary check passed: .ai/work-items/active/fix-dependency-pin-quality-routing-20260819.summary.json

### What was retained
None

### Risks
- scope: The targeted route reduces local work only for the exact classifier shape; hosted checks and all other strict changes remain full proof.

### Red reasons
None

### Human questions
- problemCount: 5
- blockedProblems: None
- resolvedProblems: quality failed before the retry.; quality failed before the retry.; quality failed before the retry.; quality failed before the retry.
- resolutionApproach: Re-ran quality after the correction; the latest attempt passed.; Re-ran quality after the correction; the latest attempt passed.; Re-ran quality after the correction; the latest attempt passed.; Re-ran quality after the correction; the latest attempt passed.
- avoidedRisks: If not detected, could have led to a stale completion claim.; If not detected, could have led to a stale completion claim.; If not detected, could have led to a stale completion claim.; If not detected, could have led to a stale completion claim.
- remainingRisks: The #907 one-line immutable action SHA diff was escalated to quality-full because generated governance paths were mixed into strict routing inputs.; The targeted route reduces local work only for the exact classifier shape; hosted checks and all other strict changes remain full proof.
- agentUnknowns: None
- humanConfirmations: None
- recurrenceLikelihood: unknown: no direct recurrence probability evidence was recorded.
- nextTime: Bind conversation locale and preserve evidence details before the next Work Item starts.
