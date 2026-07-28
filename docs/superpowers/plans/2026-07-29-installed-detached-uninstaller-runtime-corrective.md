---
author: Ray
title: "Installed Detached Uninstaller Runtime Corrective"
description: Close JA-UNINSTALL-RUNTIME-001 with an installed, digest-bound, fail-closed facts/proposal/execution lifecycle.
---

# Installed Detached Uninstaller Runtime Corrective

## Objective

Replace the non-installed in-memory removal model with an adopter-facing
three-stage lifecycle:

1. collect read-only installation facts;
2. produce a deterministic proposal bound by `proposalDigest`;
3. execute only that exact proposal, then write a truthful detached receipt.

The normal path preserves governance evidence and project-owned content. Purge
remains a separate unsupported destructive path.

## Instruction → implementation → acceptance

| Confirmed instruction or finding | Implementation surface | Verification | Acceptance |
| --- | --- | --- | --- |
| Japanese capability is mandatory and release remains blocked until real executable evidence exists. | Installed Make targets, installer catalog, Japanese assessment | Clean Japanese adopter lifecycle | A7, A8, A9 |
| Do not clear the blocker with source markers or documentation claims. | Assessment requires executable fixture and public runtime surface | Negative marker-only mutation plus adopter execution | A8, A9 |
| Preserve evidence and project-owned files by default. | Facts ownership classification, proposal preservation list, executor confinement | Preservation and drift tests | A1, A3, A4 |
| Confirmation must bind the exact operation. | Canonical facts/proposal digest and exact `--confirm-digest` | Proposal and digest mutation tests | A2, A5 |
| Partial failure must not report success. | Detached receipt records actual removed/preserved/missing/failed paths | Injected filesystem failure test | A6 |
| Installed projects must not depend on template-only files. | Catalog includes facts and executor; Makefile exposes all three stages | Clean installed-adopter test | A7 |
| Every Work Item uses bidirectional traceability and full lifecycle closure. | Contract, Summary, traceability registry, archive, PR and closure | Governance gates and Hosted terminal evidence | A10 |

## Protocol

### Phase A — facts

- Validate the installation fact bundle.
- Normalize every manifest path as repository-relative.
- Reject absolute paths, traversal, symlinks, malformed entries, and duplicate
  paths.
- Classify unchanged template-owned runtime paths as removable.
- Classify project/shared/generated/historical, modified, missing, and protected
  paths as preserved or blocking according to the fail-closed policy.
- Bind facts to the repository root identity and installation ID.

### Phase B — proposal

- Accept only valid facts for `preserve-evidence`.
- Canonically bind schema, repository identity, installation/session ID,
  removable paths with digests, preserved paths, and receipt path.
- Emit `proposalDigest` from the canonical bound payload.
- Keep proposal generation non-mutating except for its requested output JSON.

### Phase C — detached execution

- Copy the executor and its required validation modules to a system temporary
  directory; reject direct non-detached mutation calls.
- Load the proposal from outside its deletion list.
- Require exact `--confirm-digest`.
- Recollect facts immediately before mutation and compare the bound payload.
- Reject replay when the receipt already exists.
- Remove only normalized unchanged files listed in the proposal, never following
  symlinks.
- Stop on the first failure and write the actual partial state.
- Verify removed paths are absent and preserved paths remain before setting
  `runtimeRemovalVerified: true`.

## Test-first sequence

1. Add failing facts tests for deterministic output, ownership/drift, traversal,
   duplicates, and symlinks.
2. Add failing proposal tests for canonical digest binding and mutation.
3. Replace model-only detached tests with filesystem tests for confirmation,
   repository binding, replay, preservation, success, and partial failure.
4. Add installed-runtime parity and clean Japanese adopter lifecycle tests.
5. Implement the smallest protocol that satisfies those tests.
6. Regenerate the Japanese assessment and Capability Truth Matrix evidence.
7. Run focused tests, `quality-fast`, full `ai-finish`, archive, aggregate PR
   gate, Hosted CI, merge, lifecycle closure, branch cleanup, and main sync.

## STOP conditions

- Any candidate path escapes the repository or traverses a symlink.
- Installation facts are malformed, unbound, missing, drifted, or unknown-owned.
- The proposal digest, repository identity, installation ID, or current facts do
  not exactly match.
- The receipt path is inside the deletion set or already exists.
- Any deletion fails; the executor writes a partial receipt and stops.
- The installed adopter fixture cannot execute all three stages using installed
  files only.

## Problems discovered during implementation

| Problem | Process response | Regression evidence |
| --- | --- | --- |
| The transient `.ai/cockpit/.install.lock` entered the durable install manifest and made copied adopters drift immediately. | Exclude the lock at fact creation, not in the uninstaller. | `tests/test_install_facts.py`; clean-adopter lifecycle |
| The active Work Item `MODE=code`/`MODE=investigate` leaked into the uninstall mode because the public target reused the global variable. | Give uninstall its own `UNINSTALL_MODE` input. | installed Make lifecycle |
| Root README language files could be classified as Template-owned and removed. | Classify all three root README files as Project-owned. | `tests/test_install_facts.py`; preservation tests |
| The Japanese assessment could clear the blocker from source markers and public target names without executing removal in a clean adopter. | Require the clean-adopter lifecycle test in the assessment evidence. | `tests/test_japanese_capability.py`; `tests/test_japanese_adopter_lifecycle.py` |
| The first executor implementation ran from the same repository file it intended to remove, so the “detached” claim was stronger than the implementation. | Copy the complete validation runtime to a system temporary directory; block direct internal mutation and record `detachedExecution` in the receipt. | `tests/test_detached_uninstaller.py`; clean-adopter lifecycle |
| Receipt parents could be symlinked outside the repository. | Validate every receipt path component before the first deletion and use an atomic temporary receipt replacement. | `tests/test_detached_uninstaller.py` |
| The root `Makefile` was in scope but restricted-write authorization was still false. | Record the user’s existing authorization narrowly for the three uninstall targets, then refresh Preflight and checkpoints. | Contract; `make ai-checkpoint` |
| The first `quality-fast` run found two unformatted scripts and one unused import. | Remove the unused import, run the project formatter, and restart the complete fast gate rather than reusing partial results. | `make quality-fast` |
| Full quality passed all 1451 tests at 85.61% coverage but the Bandit baseline still described 111 findings after the detached executor added B404 and B603. | Review the exact LOW findings, add the protected baseline to Contract/Summary ownership, bind count 113 and the canonical digest, and rerun full Finish; do not suppress or accept medium/high findings. | `target/quality/bandit.json`; `make check-bandit-baseline`; restarted `make ai-finish` |
