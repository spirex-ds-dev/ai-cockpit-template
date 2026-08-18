# AI Cockpit Task Report

Task Result
Status: Blocked

What was completed

Implementation Approach
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

- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json [evidence: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.contract.json]
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json [evidence: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.summary.json]
- Changed .ai/cockpit/current_status.md [evidence: .ai/cockpit/current_status.md]
- Changed .ai/work-items/starts/fix-shellcheck-apt-mirror-20260819.json [evidence: .ai/work-items/starts/fix-shellcheck-apt-mirror-20260819.json]
- Changed .github/workflows/compatibility.yml [evidence: .github/workflows/compatibility.yml]
- Changed tests/test_workflows.py [evidence: tests/test_workflows.py]
- Changed .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json [evidence: .ai/evidence/reference-impact/fix-shellcheck-apt-mirror-20260819.json]
- Changed scripts/installer/legacy.py [evidence: scripts/installer/legacy.py]
- Changed tests/test_installer.py [evidence: tests/test_installer.py]
- Changed Makefile [evidence: Makefile]
- Changed tests/test_makefile.py [evidence: tests/test_makefile.py]
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.json [evidence: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.json]
- Changed .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.md [evidence: .ai/work-items/active/fix-shellcheck-apt-mirror-20260819.outcome.md]
- Changed .ai/cockpit/task_report.json [evidence: .ai/cockpit/task_report.json]
- Changed .ai/cockpit/task_report.md [evidence: .ai/cockpit/task_report.md]
- Changed docs/reference/capability-truth-matrix.json [evidence: docs/reference/capability-truth-matrix.json]
- Changed docs/reference/capability-truth-matrix.md [evidence: docs/reference/capability-truth-matrix.md]
- Changed docs/reference/japanese-capability-assessment.json [evidence: docs/reference/japanese-capability-assessment.json]
- Changed docs/reference/japanese-capability-assessment.md [evidence: docs/reference/japanese-capability-assessment.md]
- Changed docs/reference/pre-release-documentation-alignment.json [evidence: docs/reference/pre-release-documentation-alignment.json]
- Changed docs/reference/pre-release-documentation-alignment.md [evidence: docs/reference/pre-release-documentation-alignment.md]

Problems found
- Total: 4
- Blocking: 1
- Warning: 1

Stops triggered
- Reason: aiGuidelines failed before the retry. | Stage: verification | Resolution: Retry aiGuidelines after correcting the recorded failure. [evidence: verificationHistory[0] aiGuidelines failed, verification[aiGuidelines] retry passed]
- Reason: quality failed before the retry. | Stage: verification | Resolution: Retry quality after correcting the recorded failure. [evidence: verificationHistory[1] quality failed, verification[quality] retry passed]
- Reason: aiSummary failed before the retry. | Stage: verification | Resolution: Retry aiSummary after correcting the recorded failure. [evidence: verificationHistory[2] aiSummary failed, verification[aiSummary] retry passed]

Problems resolved
- Problem: aiGuidelines failed before the retry.
  Solution: Re-ran aiGuidelines after the correction; the latest attempt passed.
  Evidence: [evidence: verificationHistory[0] aiGuidelines failed, verification[aiGuidelines] retry passed]
- Problem: quality failed before the retry.
  Solution: Re-ran quality after the correction; the latest attempt passed.
  Evidence: [evidence: verificationHistory[1] quality failed, verification[quality] retry passed]
- Problem: aiSummary failed before the retry.
  Solution: Re-ran aiSummary after the correction; the latest attempt passed.
  Evidence: [evidence: verificationHistory[2] aiSummary failed, verification[aiSummary] retry passed]

Risks avoided
- If not detected, could have led to a stale completion claim. (inference)
- If not detected, could have led to a stale completion claim. (inference)
- If not detected, could have led to a stale completion claim. (inference)

Remaining risks
- The workflow fix removes the observed apt mirror dependency, but PR #906 must be revalidated on hosted CI after this corrective change merges. [evidence: residualRisks]

Unknowns
- None recorded.

Human decisions
- None recorded.

Verification
- sourceBoundEvidence [evidence: sourceBoundEvidence]
- aiWorkItem [evidence: aiWorkItem]
- aiScope [evidence: aiScope]
- aiGuards [evidence: aiGuards]
- aiCheckpoint [evidence: aiCheckpoint]
- aiReviewPolicy [evidence: aiReviewPolicy]
- aiBacktrack [evidence: aiBacktrack]
- aiCoverage [evidence: aiCoverage]
- aiScenarioCoverage [evidence: aiScenarioCoverage]
- aiGuidelines [evidence: aiGuidelines]
- aiDiffOwnership [evidence: aiDiffOwnership]
- quality [evidence: quality]
- aiStatus [evidence: aiStatus]
- aiStatusCheck [evidence: aiStatusCheck]
- aiStatusConsistency [evidence: aiStatusConsistency]
- aiAgentRisk [evidence: aiAgentRisk]
- aiSummary [evidence: aiSummary]

Impact
- Rework avoided: If not detected, could have led to a stale completion claim. (inference)
- Repeat correction prevented: unknown: no direct recurrence probability evidence was recorded. (inference)
- Major risk prevented: If not detected, could have led to a stale completion claim. (inference)

Next action
- Bind conversation locale and preserve evidence details before the next Work Item starts. (inference)
