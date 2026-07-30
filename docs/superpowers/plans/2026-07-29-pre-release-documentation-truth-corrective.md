---
author: Ray
title: "Pre-release Documentation Truth Corrective"
description: Correct release-facing evidence binding and authority boundaries before final Japanese reassessment.
keywords:
  - ai-cockpit
  - capability-truth
  - japanese
  - release-evidence
---

# Pre-release Documentation Truth Corrective
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


Work Item: `pre-release-documentation-truth-corrective-20260729`

This corrective consumes the eight consensus findings in
`docs/reference/pre-release-documentation-review.json`. It is not the final
documentation-alignment Work Item and cannot satisfy the Japanese
`final_reassessment` release prerequisite.

## Implementation map

1. Bind every Capability Truth row to normalized source/test file bytes and
   fail closed for missing, duplicate, escaping, symlinked, or changed evidence.
2. Align the Quick Install row with the implemented archive/digest mechanism
   while keeping provider publication and candidate availability as separate
   release evidence.
3. Remove highest-tag guessing from all README install fallbacks.
4. Separate repository projection, candidate, tag, provider draft/stable
   Release, assets, and freeze evidence in the three release guides.
5. Bind the Japanese assessment to every trilingual authority surface changed
   here, label this report `corrective_validation`, and require a later
   `final_reassessment` in release preflight.
6. Restore same-language navigation and one current serial plan state.
7. Resolve the structured review findings only with focused and full
   verification evidence.

## Required closure

Run focused tests and documentation checks, regenerate both evidence records,
complete full quality and `ai-finish`, push one dedicated branch, merge one PR,
run `ai-close-work-item`, remove local and remote branches/worktree, and
synchronize clean main. Then start a new Japanese final-reassessment Work Item
from corrected main; only after that closes may the paused documentation
alignment resume.

## Issues

- `DOC-TRUTH-ISSUE-001`: context-free `role` matching caused a false critical-
  domain Preflight result; precise report-classification wording restored
  `ready`, and the process false positive remains recorded.
- `DOC-TRUTH-ISSUE-002`: byte binding exposed two obsolete test evidence paths
  that row-only digests had allowed to remain green.
- `DOC-TRUTH-ISSUE-004`: the first Finish stopped before heavy tests because
  the existing Coverage Guard association omitted the exact matrix test; the
  narrow production/test pair was registered before a fresh Finish.
- `DOC-TRUTH-ISSUE-005`: the next full run passed 1480 tests and coverage but
  the quality-architecture scanner matched the validator's own parent-path
  detection literal. The same fail-closed check now uses normalized Path parts,
  with the escape regression retained, before another complete Finish.
