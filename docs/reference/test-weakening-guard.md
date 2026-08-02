---
author: Ray
title: "Test Weakening Guard"
description: Diff-derived warning, review, and block decisions for reduced test verification strength.
audience:
  - adopter
  - maintainer
status: current
authority: canonical
lastVerifiedBy: capability-truth-matrix
capabilityClaims:
  - test_weakening_guard
keywords:
  - ai-cockpit
  - test-weakening
  - evidence
---
# Test Weakening Guard

The Test Weakening Guard compares a declared Git base with the current worktree and emits reproducible evidence when verification strength may have been reduced. Agent prose is not passing evidence. The guard never claims that an empty signal list proves semantic equivalence or adequate coverage.

## Use and quality ownership

```sh
make check-ai-test-weakening-fast
make check-ai-test-weakening
make check-ai-pr AI_BASE_COMMIT=<merge-base-sha>
```

Fast mode checks low-cost signals such as added skips, test deletion, CI nonblocking changes, and explicit success bypasses. Full mode also compares test cases, assertions, exception assertions, negative tests, coverage scope and threshold configuration, test-command scope, and snapshot churn. `quality-fast` owns fast mode only when run by itself. `quality-full` and `quality-release` suppress that duplicate and run full mode once. `check-ai-pr` always runs full mode against `AI_BASE_COMMIT`.

If `--base-ref` is omitted, the checker uses the sole active Contract's `baseCommit`; without an active Contract it uses `HEAD`, which makes a clean base a no-op. The policy is `.ai/guards/test_weakening_policy.yaml`, and the report schema is `.ai/schemas/test_weakening.schema.json`.

## Decisions

- `continue`: no configured static weakening signal was found. This is not proof that the tests are sufficient.
- `warning`: a file rename, a case rename/refactor that preserves case and assertion counts without removing protected negative/security/regression semantics, a small snapshot change, a minor assertion reduction, or apparent condition relaxation needs reviewer attention but does not stop the command.
- `review`: material assertion loss, added skip, removed case or exception/negative assertion, coverage or test-command scope reduction, nonblocking required check, general test deletion, or large snapshot churn requires explanation and independent requirement evidence.
- `block`: explicit requests to delete or disable failing tests, security or regression test deletion, `continue-on-error`, `allow_failure`, `|| true`, or coverage lowering expressly intended to make the current result pass are rejected.

Every non-continue report contains a recovery condition. Restore the lost test strength, or provide independently reviewable changed-requirement evidence and rerun against the same base. A narrative such as “the tests are safe” does not clear a signal.

For an intentional retirement, `.ai/evidence/test-weakening/*.json` may authorize
only review-level signals. Its `baseRef`, `retiredPaths`, and `allowedSignals`
must exactly match the live report, and it must carry a non-empty human
authorization reference and digest. Accepted evidence changes the result to a
visible `warning`; missing, stale, mismatched, malformed, or critical-signal
evidence remains fail-closed.

## Evidence and compatibility

```json
{
  "version": 1,
  "mode": "full",
  "baseRef": "0123456789abcdef",
  "decision": "review",
  "signals": [
    {
      "type": "assertion_reduction",
      "path": "tests/test_order.py",
      "before": 12,
      "after": 5,
      "severity": "high"
    }
  ],
  "requiredExplanation": true,
  "recoveryCondition": "Restore test strength or provide independently reviewable changed-requirement evidence.",
  "limitations": ["Static signals do not prove semantic equivalence or complete test coverage."]
}
```

Pre-version reports containing `decision`, `signals`, and `requiredExplanation` can be read as legacy version 0. They are normalized to version 1 with `legacySourceVersion: 0` and a mandatory renewed-analysis recovery condition; missing Git evidence is never invented. Unknown future versions and malformed policy fail closed.

## Limits

The analysis is language- and framework-neutral text comparison. Files containing NUL bytes or bytes that are not valid UTF-8 are treated as binary and excluded from text-semantic signals; this prevents compiler artifacts with test-like paths from being interpreted as source, but it does not inspect binary test semantics. Replacing a text file with binary content still analyzes the removed text as a potential weakening. The guard can report legitimate test consolidation, generated snapshot changes, or renamed concepts as false positives. It can miss helper-level semantic relaxation, data-driven case loss, custom skip mechanisms, provider-side required-check changes, or behavior hidden by generated and dynamic tests. A skipped case in a newly added test file is incomplete new evidence, not a weakening of baseline evidence, so this guard does not report it as `skip_added`. Thresholds only select review intensity; they do not define safety. External CI/provider state remains outside repository evidence.

Repository paths are normalized and must remain inside the worktree. Invalid revisions, traversal, non-files, and symbolic links escaping the repository fail closed. The checker reads and reports; it never edits tests, coverage configuration, workflows, or provider settings.
