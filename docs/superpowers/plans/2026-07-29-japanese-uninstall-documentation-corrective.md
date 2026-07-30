---
author: Ray
title: "Japanese Uninstall Documentation Corrective"
description: Prompt-first, evidence-preserving Japanese uninstall guidance and a mutation-resistant JA-DOC-001 gate.
keywords:
  - ai-cockpit
  - japanese
  - uninstall
  - documentation
  - fail-closed
---

# Japanese Uninstall Documentation Corrective
> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**


## Objective

Close `JA-DOC-001` with an actionable Japanese engineer path, not with the
mere presence of the word “uninstall.” The procedure must be usable by a
person with no programming experience, remain version-neutral, preserve
evidence by default, and describe only behavior implemented by the installed
lifecycle. Implementation review found that the installed repository currently
has only a proposal entrypoint that writes one proposal JSON without changing
Runtime. The detached-removal model exists only in template source, is not
installed, and does not remove files. The guide therefore stops at that
boundary and the release assessment creates the separate blocker
`JA-UNINSTALL-RUNTIME-001`.

Here, “proposal” means a reviewable JSON file that does not delete Runtime.
“Detached executor” means a separately launched public tool that really
changes filesystem state and verifies the result. The current Work Item fixes
documentation and release-assessment truth; the next Work Item implements the
missing runtime capability.

## Instruction → plan → implementation → acceptance

| Instruction | Plan | Implementation evidence | Acceptance evidence |
| --- | --- | --- | --- |
| Japanese capability is mandatory before release. | Keep `JA-DOC-001` blocking until the complete procedure exists, then keep the newly discovered runtime gap independently blocking. | `scripts/ai_japanese_capability.py`; generated assessment | `tests/test_japanese_capability.py`; assessment check |
| Installation and removal must be simple for a beginner. | Add copy-ready prompts with purpose, PASS, STOP, and owner at every phase. | `docs/getting-started/installation.ja.md` | `tests/test_docs_metadata.py`; native-language review |
| Prefer prompts over unexplained commands. | Delegate facts collection, proposal generation, execution, and verification to the agent; expose only the real proposal target and explain it. | Japanese installation, upgrade, and troubleshooting routes | documentation mutation tests |
| Never lose evidence silently. | Default to `preserve-evidence`; keep project-owned, modified, drifted, and unknown-owned files; stop if no public detached executor can produce a final receipt. | Japanese uninstall section aligned to current implementation evidence | marker and semantic-boundary checks |
| Purge is separately destructive. | Require evidence export, exact deletion review, irreversible-impact review, and a second bounded confirmation. | Japanese purge subsection | missing-purge-confirmation mutation |
| Avoid fixed release versions. | Describe behavior through the installed repository entrypoint and current installed lifecycle. | version-neutral Japanese prompts | hardcoded-version regression |
| Prevent recurrence. | Replace keyword detection with ordered actionable markers shared by the docs gate and Japanese release assessment. | assessor and docs checker | keyword-only and missing-step regressions |
| Correct existing overclaims. | Align Installed Lifecycle and the Capability Truth Matrix with the installed catalog, proposal writes, absent facts builder/digest binding, and non-installed model boundary. | `docs/reference/installed-lifecycle.md`; capability matrix | capability-matrix and Japanese assessment regressions |
| Complete governed delivery before continuing. | Finish, archive, PR, Hosted CI, merge, lifecycle closure, branch cleanup, and base sync. | Contract/Summary/Manifest and PR | `ai-finish`, Hosted checks, `ai-close-work-item` |

## Execution sequence

1. Add red tests proving a keyword-only document cannot clear `JA-DOC-001`.
2. Define the ordered actionable uninstall contract and expose it through the
   documentation checker and Japanese assessment.
3. Add the prompt-first Japanese procedure and same-language routes from
   upgrade and troubleshooting.
4. Regenerate the JSON/Markdown Japanese assessment from repository bytes.
5. Record `JA-UNINSTALL-RUNTIME-001` and its independent corrective Work Item;
   do not claim that the current model deletes files.
6. Map this instruction, plan, implementation, and acceptance evidence in the
   machine traceability registry and comprehensive plan.
7. Run focused mutation tests, docs metadata, Japanese assessment, fast and
   full quality, then archive and deliver through one PR.
8. Merge, close the Work Item, delete its local and remote work branch,
   synchronize `main`, and only then begin the detached-runtime corrective.
