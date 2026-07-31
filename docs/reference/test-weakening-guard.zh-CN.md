---
author: Ray
title: "Test Weakening Guard"
description: 基于 Git 差异证据，将测试验证强度下降分类为 warning、review 或 block。
audience:
  - adopter
  - maintainer
status: current
authority: translation
canonical: docs/reference/test-weakening-guard.md
lastVerifiedBy: capability-truth-matrix
keywords:
  - ai-cockpit
  - test-weakening
  - evidence
---
# Test Weakening Guard

Test Weakening Guard 比较声明的 Git base 与当前 worktree，为可能降低测试验证强度的变化生成可复核证据。Agent 的文字说明不能作为通过证据。即使 Signal 为空，也不代表系统证明了语义等价或 Coverage 充分。

## 使用与质量图归属

```sh
make check-ai-test-weakening-fast
make check-ai-test-weakening
make check-ai-pr AI_BASE_COMMIT=<merge-base-sha>
```

Fast 只检查低成本 Signal，例如新增 Skip、删除测试、把 CI 改成非阻塞以及明确的成功绕过。Full 还比较 Test Case、Assertion、异常 Assertion、Negative Test、Coverage 范围和门槛、测试命令范围与 Snapshot churn。单独运行 `quality-fast` 时由 Fast 模式负责；`quality-full` 和 `quality-release` 会跳过重复 Fast，仅运行一次 Full。`check-ai-pr` 始终针对 `AI_BASE_COMMIT` 运行 Full。

省略 `--base-ref` 时，Checker 使用唯一 Active Contract 的 `baseCommit`；没有 Active Contract 时使用 `HEAD`。Policy 位于 `.ai/guards/test_weakening_policy.yaml`，Schema 位于 `.ai/schemas/test_weakening.schema.json`。

## 判定与恢复

- `continue`：未发现已配置的静态削弱 Signal；这不是测试充分的证明。
- `warning`：文件重命名、在不减少用例与断言数量且不移除受保护的负向/安全/回归语义时进行的用例重命名或重构、小范围 Snapshot 变化、轻微 Assertion 减少或疑似条件放宽只提示 Reviewer。
- `review`：Assertion 大幅减少、新增 Skip、删除 Case/异常/Negative Test、缩小 Coverage 或测试命令范围、把 Required Check 改为非阻塞、一般测试删除或大规模 Snapshot churn，需要解释和独立可审查的需求变更证据。
- `block`：明确要求删除或关闭失败测试、删除 Security/Regression Test、增加 `continue-on-error`、`allow_failure`、`|| true`，或为了让当前结果通过而降低 Coverage，均直接拒绝。

恢复方式是还原测试强度，或提供独立可审查的需求变更证据，然后针对同一个 base 重新运行。“我确认安全”一类自我声明不能清除 Signal。

没有 Version 的旧 Report 只有在包含 `decision`、`signals` 和 `requiredExplanation` 时才按 version 0 读取，并规范化为带 `legacySourceVersion: 0` 的 version 1，同时要求重新分析；系统不会编造缺失的 Git 证据。未知未来 Version 或损坏 Policy 均 fail closed。

## 限制

该分析是与语言和测试框架无关的文本差异比较。包含 NUL 字节或无效 UTF-8 字节的文件会被视为二进制内容，不参与文本语义 Signal；这避免把测试路径下的编译产物误当作源代码，但不会检查二进制测试语义。如果文本文件被二进制内容替换，Guard 仍会把被移除的文本作为潜在削弱进行分析。合法的测试合并、生成 Snapshot 或概念重命名可能产生 False Positive；Helper 内的语义放宽、Data-driven Case 丢失、自定义 Skip、Provider 端 Required Check，以及动态或生成测试可能形成 False Negative。新测试文件中的 Skip Case 属于不完整的新 Evidence，而非削弱 Baseline Evidence，因此本 Guard 不将其报告为 `skip_added`。阈值只决定审查强度，不定义安全。外部 CI/Provider 状态不属于 Repository Evidence。

路径必须规范化并保持在 worktree 内。无效 Revision、Traversal、非常规文件或指向仓库外的 Symbolic Link 会 fail closed。Checker 只读取和报告，不会修改测试、Coverage、Workflow 或 Provider 设置。
