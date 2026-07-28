---
author: Ray
title: "Installation"
description: Prompt-first, beginner-safe installation and adoption guide for AI Cockpit.
keywords:
  - ai-cockpit
  - installation
  - beginner
  - prompt-first
  - ai-agents
---

# Installation

This is the complete English hand sequence. You do not need programming
experience. Your AI coding agent may inspect and prepare work, but you remain
the decision maker. Installation copies the governance Runtime; calibration,
the first pull request, hosted CI, merge, and lifecycle closure are separate
steps.

Read the [Capability Truth Matrix](../reference/capability-truth-matrix.md) for
what is currently implemented. For a shorter entry, use
[30-Second Start](30-second-start.md); for security evidence, use
[Security and Release Verification](security-release-verification.md).

<!-- prompt-safety: read-only-discovery -->
<!-- prompt-safety: explain-evidence-unknowns -->
<!-- prompt-safety: plan-before-write -->
<!-- prompt-safety: human-confirmation-before-write -->
<!-- prompt-safety: no-downstream-authority -->
<!-- prompt-safety: preserve-user-changes -->

## How to use this guide

At each numbered stage:

1. copy the prompt into the agent that has your project open;
2. wait for the stated result;
3. stop if the result differs or contains an unknown;
4. approve only the current stage, never all later stages at once.

“Repository” means the project folder tracked by Git. “Worktree” means the
files currently visible in that folder. “PR” means pull request: a review page
for proposed changes.

<!-- novice-stage: before-you-start -->
## 1. Before you start

You need the project on your computer, an AI coding agent that can inspect that
folder, Git, Python 3.10 or newer, GNU Make, and at least one existing Git
commit. You also need permission to create a branch and PR in the project.

Git keeps the project's change history. A commit is one reviewed snapshot in
that history. Python and GNU Make run AI Cockpit's local checks. You do not
need to know whether they are installed: do not install them yourself yet;
paste this prompt and let the agent check without changing the project:

```text
Before AI Cockpit installation, identify this computer's operating system and
check the project folder, AI coding-agent access, Git, Python version, GNU
Make, curl, initial Git commit, and branch/PR permission. Change nothing.
For every item show: plain-language purpose, observed evidence, PASS or STOP,
and the person/team to contact if it is missing. Do not suggest an unapproved
tool installer. End only when I can see whether Step 1 is safe to continue.
```

Do not install into the AI Cockpit template repository by mistake. Back up
irreplaceable local work. If you are unsure whether the correct folder is
open, stop—the next prompt will identify it without changing anything.

Expected result: you know which project you intend to govern and who can
review its first PR.

<!-- novice-stage: open-your-project -->
## 2. Open your project

Open the project folder in your AI coding agent. Do not create files yet.

Copy:

```text
Show only: the folder currently open, whether it is the root of one Git
repository, the current branch, and the number of changed and untracked files.
Change nothing. Explain every line in plain language. STOP if this is not a
Git repository root, if it is the AI Cockpit template rather than my project,
or if any existing change is not understood. Tell me who owns the project if
that can be proven; otherwise write Unknown.
```

Expected result: the agent names the intended Git root and reports zero
changes, or explains and preserves every existing change. If the wrong folder
is open, open the intended project and repeat Step 2.

<!-- novice-stage: copy-discovery-prompt -->
## 3. Copy the read-only discovery prompt

Copy everything in the following text block:

```text
I want to install AI Cockpit in this project. Work read-only first.
Use the canonical public source
https://github.com/spirex-ds-dev/ai-cockpit-template.git and public metadata
https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/main/release.json
unless I provide an explicitly verified private mirror. Resolve a fixed tag and
report its tag target, source commit, installer digest, archive asset and
SHA-256 evidence; stop if any required published evidence is missing/mismatched.
Do not create, edit, delete, commit, push, open or merge a PR, or publish.
Preserve every unrelated user change.

Inspect and explain in plain language:
1. the repository root, current branch, worktree status, and whether an initial
   commit exists;
2. the remote whose HEAD identifies the default branch, that branch name, and
   its latest fetched commit—do not assume origin or main;
3. whether Python 3.10+, Git, GNU Make, and curl are available;
4. the detected languages/build systems and the best AI Cockpit stack choice;
5. existing AGENTS.md, GEMINI.md, CLAUDE.md, Makefiles, CI workflows, security
   policy, CODEOWNERS, and active .ai Work Items;
6. generated files, critical paths, tests, coverage, and quality commands that
   are evidenced by project files;
7. every fact that is unknown or only inferred.

Separate Observed Evidence, Inference, and Unknowns. Explain each technical
term. If the worktree is dirty, there is no initial commit, required tools are
missing, the default branch cannot be proven, or an active Work Item exists,
stop and give recovery instructions. Otherwise propose an installation plan
with the exact files and Wizard choices. Do not write anything until I
explicitly approve that plan.
```

Expected result: a read-only report, not a changed-file list. If the agent
changed anything, stop and restore only changes the agent can prove it made;
do not discard pre-existing user work.

<!-- novice-stage: review-read-only-report -->
## 4. Review the discovery report

Check these lines one by one:

- the folder is the intended project;
- the worktree is clean, or every existing change is understood and preserved;
- an initial commit exists;
- the remote/default branch came from evidence, not an `origin/main` guess;
- Python is at least 3.10 and Git, Make, and curl were found;
- the stack recommendation matches the project;
- unknowns are visible rather than guessed.

Copy:

```text
Guide me through the seven review items above without changing anything. For
each item show its plain-language meaning, exact observed evidence, PASS or
STOP, and the person/team to contact on STOP. Ask me whether I understand the
current item, then wait before showing the next. Do not hide an Unknown or
start installation.
```

The following is an **advanced manual fallback** for direct worktree evidence.
Run it only from the intended repository root.

Purpose: show changed and untracked files. Success: no output, or only changes
you already understand. Failure response: do not install; ask the agent to
explain each line and preserve it.

<!-- command-guide: purpose,success,failure -->
<!-- command-evidence: adopter_required -->
```sh
git status --short
```

<!-- novice-stage: choose-wizard-options -->
## 5. Review the Wizard mode and installer defaults

The current interactive Wizard asks only for the mode: New Adoption, Upgrade,
or Dry Run. Stack is detected; branch/base is detected; other values below are
fixed Wizard defaults or CLI/environment controls, not extra Wizard screens.
Ask the agent to explain and record the interaction model:

First paste this prompt. It prevents you from having to interpret the technical
option names yourself:

```text
Using only the read-only report, explain the one selectable Wizard mode and
every detected/fixed default or CLI/environment control below. Return a table
with: selectable/detected/fixed/CLI-only, plain-language meaning, current
value, observed evidence, safe recommendation, and STOP condition. Mark
Unknown and ask for expert help instead of guessing. Do not run or write.
```

| Kind | Item | Normal behavior |
| --- | --- | --- |
| Selectable | Mode | **New Adoption** for a project without AI Cockpit; **Upgrade** only for an existing installation; **Dry Run** to preview without writing. |
| Bootstrap evidence | Source | The beginner route supplies a published fixed release. A local clone/private mirror is an explicit non-public trust path. |
| Detected | Stack | The Wizard currently auto-detects Python, Swift, and Android signals; absent, other, or mixed signals use `generic`. Another stack may be supplied only by the scripted `--stack` control after evidence review; it is not a Wizard question. |
| Detected | Base/branch | The installer derives remote/default-branch evidence; `--create-adoption` creates the adoption branch for New Adoption. |
| Fixed default | Make integration | Off in the Wizard (`update_makefile=false`); scripted installs may use `--update-makefile` after conflict review. |
| Fixed default | Examples | Off (`with_examples=false`); `--with-examples` is a scripted option and never proves the stack works. |
| Fixed default | Glossary replacement | Off (`replace_glossary=false`); scripted `--replace-glossary` requires explicit content review. |
| Entry mode | Interactive | `--interactive` enters plan review and final write confirmation. |

Normal safe behavior is New Adoption, canonical published fixed release,
the detected stack (otherwise `generic`), a dedicated adoption branch, no Make
integration, no optional examples, preserve the existing glossary, and
interactive plan review. Stop for the repository owner if any default conflicts
with existing files or organization policy.

Maintenance-only options are `--upgrade` and `--upgrade-with-active`.
`--dry-run` must remain read-only. `AI_COCKPIT_TEMPLATE_REF` selects an
explicit source ref; `AI_COCKPIT_TEMPLATE_SHA256` is only an additional
assertion and cannot replace published release metadata.

For iOS, Android, or Java, open the same-language example before choosing:
[iOS](examples/ios.md), [Android](examples/android.md), [Java](examples/java.md).

<!-- novice-stage: review-installation-plan -->
## 6. Review the installation plan

Copy this prompt:

```text
Show the final installation plan without writing. Include the fixed release
identity and trust evidence, fetched base commit, new branch, stack, every
installer option, every file to create/modify/preserve, conflicts, rollback
behavior, and post-write checks. Explain why each choice fits this repository.
Mark Unknown instead of guessing. End with one yes/no question asking whether
you may perform only the scaffold write and its validation. Do not authorize
commit, push, PR, merge, release, deletion, or calibration activation.
```

Expected result: an exact plan and one bounded confirmation question. Reject
the plan if it uses a moving branch, assumes a default branch, hides conflicts,
or combines later authority.

<!-- novice-stage: approve-scaffold-write -->
## 7. Approve only the scaffold write

If the plan is correct, answer that the agent may execute the listed
installation transaction and validation only. The installer validates markers
and conflicts, discovers/fetches the default base, creates the adoption branch,
writes managed files, and rolls back the partial transaction on failure.

Expected result: a dedicated adoption branch and a validation report. No
commit, push, PR, merge, or release.

Before approving, verify seven visible rows: target folder, clean worktree,
fixed release evidence, fetched default-branch commit, exact changed files,
conflicts, and rollback. Then copy this exact bounded approval:

```text
I approve only the scaffold write and post-write validation exactly as listed
in the reviewed plan. Preserve unrelated user changes and stop on any new
path, conflict, Unknown, or validation failure. This does not authorize
commit, push, PR creation, merge, branch deletion, release, or Calibration
activation. After writing, show the categorized changed-file and validation
report and wait.
```

<!-- novice-stage: inspect-scaffold -->
## 8. Inspect every scaffold category

Ask the agent for a table with **category, path, created/changed/preserved,
purpose, and validation**. Review:

```text
Inspect the installed scaffold without changing it. In this exact order review
(1) agent entrypoints, (2) glossary/policy/guard/trust/profile files,
(3) adoption Contract/Summary/start receipt, (4) scripts and Make integration,
(5) Cockpit Status/evidence, (6) CI integration, and (7) optional examples.
For every category show expected paths, actual paths, created/changed/preserved,
plain-language purpose, validation result, and conflict/recovery action.
STOP on a missing required path, unplanned path, invalid generated record, or
unresolved conflict. Do not finish, commit, push, or calibrate.
```

- `AGENTS.md` and optional Gemini/Claude/Cursor agent entrypoints;
- `.ai/glossary.md`, policies, guards, trust schemas, and project profile;
- `.ai/work-items/active/` Contract/Summary and start receipt;
- `scripts/`, `Makefile.ai`, `Makefile.ai.stack`, and Makefile integration;
- status/evidence output under `.ai/cockpit/`;
- existing CI files and the CI changes that must be owned later by the separate
  configuration Work Item; the installer does not select or install hosted CI;
- optional `examples/`.

Review the seven rows one at a time. Copy only the request in the current row:

<!-- scaffold-review-table: copy-request,expected,pass,stop -->
| Category | Copy request | Expected visible result | PASS | STOP and recovery |
| --- | --- | --- | --- | --- |
| 1. Agent entrypoints | “Show only installed or preserved agent instruction files and explain which agents read each one.” | Paths such as `AGENTS.md`; existing adopter instructions are marked preserved or deliberately merged. | Every path was planned and its reader is known. | Unplanned replacement or conflicting instruction; contact repository owner and revise the plan. |
| 2. Governance files | “Show glossary, policy, guard, trust, and Project Profile paths. Explain which are defaults and which still require Calibration.” | `.ai/` paths grouped by purpose; no claim that defaults fit the project. | Required managed files validate and uncalibrated values are explicit. | Missing/invalid file or project-specific claim without evidence; rerun installer validation or contact owner. |
| 3. Work Item records | “Show the adoption Contract, Summary, and start receipt. Map their scope to every installation change.” | One active `adopt_ai_cockpit` record set. | Scope covers every changed path and only adoption. | Missing record, placeholder, or out-of-scope path; update records before any further write. |
| 4. Scripts and Make | “Show installed scripts, `Makefile.ai`, `Makefile.ai.stack`, and any reviewed Makefile edit. Explain each public entrypoint.” | Runtime files and whether Make integration was intentionally on/off. | Files validate and existing targets were preserved. | Collision, executable failure, or unplanned Make edit; stop and use conflict recovery. |
| 5. Status and evidence | “Read the current Cockpit Status and installation evidence without regenerating them; compare them with the active Contract and actual diff.” | Existing `.ai/cockpit/` output is shown beside the current Work Item. | No stale, missing, or contradictory state. | Status mismatch; show a regeneration plan and stop for separate write approval. |
| 6. CI boundary | “Show existing CI files unchanged and list the exact CI gaps for the later configuration Work Item. Do not edit CI now.” | Existing workflow evidence plus a written gap list. | No installer claim that hosted CI was installed or passed. | Unexpected CI edit or unknown required jobs; preserve the file and contact CI owner. |
| 7. Optional examples | “Show whether examples were requested, every installed example path, and why examples are not proof of this project’s stack.” | Either no examples, or only the approved example paths. | Choice matches the plan. | Unrequested example or capability overclaim; remove only through a revised, approved plan. |

If row 5 is stale, copy this separately:

```text
Show the exact Cockpit Status regeneration command, files it would change,
expected diff, validation, rollback, PASS/STOP, and repository owner. Do not
run it. Ask one yes/no question for this regeneration only and wait.
```

The source repository's `templates/` and template supply-chain evidence are
not adopter payload. Creating scaffold files does not prove calibration,
project quality, CI, platform tooling, or production readiness.

Expected result: every changed path is explained and belongs to the adoption
Work Item. If a path is unexplained or outside the approved plan, stop.

### Close the Adoption Work Item before calibration
<!-- lifecycle-order: adoption-close-before-configuration -->

The adoption branch must complete its own lifecycle first. Do not combine the
following decisions.

**A. Finish and archive locally.** Copy:

```text
Complete only the local finish of adopt_ai_cockpit. Map each acceptance item
to a changed file and verification result, update its Summary, run declared
checks and the before_finish checkpoint, archive with ai-finish, and show the
complete diff. Do not commit, push, create a PR, merge, delete a branch, close
the Work Item, or start configuration. Stop for my review.
```

PASS: the archive and exact diff are visible and all checks are recorded.
STOP: any failed check, unexplained path, missing acceptance evidence, or user
change. Ask the repository owner before continuing.

**B. Commit only the reviewed archive.** After reviewing the diff, copy:

```text
I approve one local commit containing only the reviewed adopt_ai_cockpit
archive bundle. Commit it with a clear adoption message, show the commit ID
and clean-worktree evidence, then stop. This does not authorize push, PR,
merge, branch deletion, closure, or configuration.
```

PASS: one local commit and no uncommitted adoption changes. STOP if the commit
contains an unreviewed path.

**C. Push and prepare review.** After a separate decision, copy:

```text
I approve pushing only the adopt_ai_cockpit branch and preparing its PR
against the previously evidenced default branch. Keep the source branch,
disable auto-merge and provider branch deletion, show the PR link and required
hosted checks, then stop. Do not merge or close the Work Item.
```

PASS: the PR is open against the correct base and the source branch remains.
STOP for push rejection, wrong base, missing required check, or Head SHA
mismatch. Ask the repository/CI owner.

**D. Human review and merge.** A person reviews **Files changed**,
**Conversation**, and **Checks**, then manually merges only after required
checks pass. The agent must not treat “PR created” as “merged.”

<!-- lifecycle-approval: adoption-closure-plan -->
**E1. Review the closure plan.** After the human merge, copy:

```text
The human has merged the adopt_ai_cockpit PR. Read-only verify PR ownership,
the merged commit, archived evidence, exact closure command, affected branch,
and every closure validation. Change nothing and stop for my decision.
```

PASS: ownership, archive, merged commit, branch, and plan agree. STOP: any
mismatch; send the plan and evidence to the repository owner.

<!-- lifecycle-approval: adoption-closure-execute -->
**E2. Approve closure only.** If E1 passed, copy:

```text
I approve lifecycle closure only for adopt_ai_cockpit using the reviewed plan.
Run ai-close-work-item, verify remote/local adoption branch deletion, clean
worktree, fast-forward-only base synchronization, and equality with the remote
default branch. Stop and show each result. On any failure preserve the branch
and evidence and contact the repository owner. Do not start configuration.
```

Expected result: the adoption PR is human-merged, `adopt_ai_cockpit` is closed,
its branch is deleted locally and remotely, and the local default branch equals
the remote default branch. Only then proceed.

<!-- novice-stage: complete-calibration -->
## 9. Complete all ten calibration stages

Start a separate `configure_ai_cockpit` Work Item only after the adoption Work
Item's PR is merged and lifecycle closure is verified. The agent may run
`make cockpit-doctor`, generate a proposal with `make cockpit-calibrate`, and
drive the installed resumable interface through
`make cockpit-calibrate-session ARGS="..."`. The template-maintenance-only
`make cockpit-calibration-wizard` target is not installed into adopter
projects. Prefer the copy-ready agent prompts below; the agent must show
evidence and wait for Reviewer and Owner confirmation before activation.

Use this answer vocabulary at every stage:

- **yes/no:** confirms or rejects the proposed fact;
- **alternative input:** supplies the correct value;
- **unknown:** evidence is missing; this blocks readiness;
- **not applicable:** only with a written reason.

Copy this calibration prompt:

```text
Start the configure_ai_cockpit Work Item from the newly synchronized default
branch. Guide all ten Calibration stages in order. For each stage show:
plain-language question, repository files inspected, observed evidence,
inference, Unknowns, proposed answer type/value, files the Candidate would
change, PASS/STOP condition, and who must review. Accept only yes/no,
alternative_input, unknown, or not_applicable with a reason. Do not invent
quality commands or convert missing evidence to N/A. Pause after every stage
for my answer. After Stage 10, show the complete Candidate and inventory;
require separate Reviewer and Owner confirmations before activation. Do not
commit, push, create a PR, merge, release, or close the Work Item.
```

At each pause, success means the evidence and proposed answer are understandable
to you and no blocking Unknown remains. If not, answer “Unknown—stop” and ask
the named project/platform owner for evidence.

Review every stage. The “copy request” is what a beginner sends to the agent
at that pause. The agent records the answer through the Session interface only
after the user decides.

<!-- calibration-review-table: copy-request,example,pass,stop -->
<!-- calibration-stage: repository-role -->
<!-- calibration-stage: language-and-stack -->
<!-- calibration-stage: source-boundaries -->
<!-- calibration-stage: test-boundaries -->
<!-- calibration-stage: generated-artifacts -->
<!-- calibration-stage: critical-paths -->
<!-- calibration-stage: quality-commands -->
<!-- calibration-stage: review-requirements -->
<!-- calibration-stage: risks-and-unknowns -->
<!-- calibration-stage: adoption-readiness -->
| Stage | Copy request | Example evidence and plain meaning | PASS | STOP and contact |
| --- | --- | --- | --- | --- |
| 1. Repository role | “Show evidence for whether this is an application, library, monorepo, template, or other role. Explain who releases or deploys it. Do not record an answer yet.” | A release workflow plus an app manifest may indicate an application; this is still a proposal. | The role and release owner are evidenced and understood. | Role or owner is Unknown; contact repository owner. |
| 2. Language and stack | “List manifests, language versions, package/build tools, and why one preset is only a starting point. Show alternatives.” | `pom.xml` suggests Java/Maven; it does not prove the required JDK exists. | Versions and preset fit are evidenced. | Mixed or unsupported layout; contact platform owner. |
| 3. Source boundaries | “List maintained production-source folders and separately list vendor, generated, cache, and build output. Explain every exclusion.” | `src/main/` may be maintained source; `build/` is output only when project evidence confirms it. | Every included/excluded path has an owner and reason. | A path may contain maintained code; contact module owner. |
| 4. Test boundaries | “Map unit, integration, UI/device, fixtures, and test-generated paths. Do not call one test type proof of another.” | `src/test/` and `src/androidTest/` are different evidence. | Test types and required environments are distinct. | Test ownership/environment is Unknown; contact test/platform owner. |
| 5. Generated artifacts | “List generated paths, generator, source of truth, regeneration command, and whether direct edits are forbidden.” | A generated client is not source of truth when its schema and generator are known. | Generator and drift rule are evidenced. | Generator/ownership missing; contact build owner. |
| 6. Critical paths | “Identify security, release, migration, payment, identity, signing, deployment, and project-specific high-risk paths with required reviewers.” | A signing workflow may require the release owner even when tests pass. | Each critical path has a human reviewer. | High-risk ownership is missing; contact security/release owner. |
| 7. Quality commands | “Copy exact quality commands only from repository or CI evidence. Show prerequisites, purpose, success output, and failure action.” | A CI command proves syntax used there, not that local SDKs are installed. | Every required command has evidence and expected result. | Command would be invented or prerequisites missing; contact build/CI owner. |
| 8. Review requirements | “Show CODEOWNERS, branch protection, required hosted checks, and actions the agent cannot authorize.” | CODEOWNERS suggests reviewers; provider settings prove enforcement. | Human owners and required checks are explicit. | Provider evidence unavailable; contact repository administrator. |
| 9. Risks and unknowns | “List every unresolved fact with consequence, owner, and recovery. Do not change Unknown to N/A.” | Missing device access remains blocking for a required device test. | No hidden blocking Unknown remains. | Any blocking Unknown; contact its named owner. |
| 10. Adoption readiness | “Show all answers, Candidate diff, inventory, checks, residual limits, and separate Reviewer/Owner decisions. Do not activate yet.” | A complete Candidate is reviewable evidence, not approval. | Full self-check passes and both humans explicitly confirm. | Missing/stale evidence or rejected answer; return to that stage. |

Expected result: a reviewable Candidate and inventory with no hidden Unknown.
Activation is atomic and preserves the previous Active configuration on
failure; this does not prove enterprise compliance or runtime sandboxing.

<!-- novice-stage: run-local-checks -->
## 10. Run local checks

Ask the agent:

```text
Run only the local checks declared by the active Contract. Explain each check
before running it. Stream progress, record actual pass/fail/not-run evidence,
and stop on failure. Do not weaken, skip, or relabel a gate. Do not commit,
push, open a PR, merge, or release.
```

The readiness sequence must include these exact repository targets:

<!-- public-quality-target: ai-cockpit-quality -->
```text
make ai-cockpit-quality
make check-ai-adoption-ready
```

Purpose: run project quality, then verify adoption evidence. Success: both
commands exit successfully and the Summary records them. Failure response:
stop, keep the failure output, and correct the Contract/configuration or
project problem in the same Work Item.

<!-- novice-stage: complete-first-work-item -->
## 11. Complete the configuration Work Item

The agent now completes `configure_ai_cockpit`: it updates the Summary, runs the `before_finish` checkpoint and
`make ai-finish TASK=<task>`, archives the Contract/Summary, and presents the
exact diff and verification. If no active Contract/Summary is supplied,
`make check-ai-status` may report
`Skipping status check (no active contract/summary provided)`; use
`make check-ai-status-consistency` to validate the no-active state.

Human decision: approve the archive-evidence commit only after reviewing the
diff. A commit approval is not push approval.

Copy:

```text
Finish only configure_ai_cockpit. Show each Contract acceptance item beside
its implementation and test evidence, run before_finish and ai-finish, then
show a plain-language diff grouped as profile, guards, quality commands, CI,
and archive evidence. Stop for my commit decision. Do not push or open a PR.
```

After reviewing the diff, use a second prompt:

```text
I approve one local commit containing only the reviewed configure_ai_cockpit
archive bundle. Commit it, show its commit ID and clean-worktree evidence, then
stop. Do not push, create a PR, merge, delete a branch, or close the Work Item.
```

PASS: one reviewed configuration commit and a clean worktree. STOP: any
unreviewed file or failed check; contact the repository owner.

<!-- novice-stage: review-pr-and-hosted-ci -->
## 12. Review the PR and hosted CI

After a separate push approval, copy:

```text
Push only the configure_ai_cockpit branch and prepare its PR against the
evidenced default branch. Keep the source branch, disable auto-merge and
provider branch deletion, and show the PR link, Head SHA, and required hosted
jobs. Stop. Do not merge or close the Work Item.
```

PASS: correct base/Head SHA, PR link, and all required jobs are visible. STOP:
push rejection, wrong base/SHA, missing or skipped required job; contact the
repository or CI owner.

The PR
must target the discovered default branch and keep its source branch for
lifecycle closure. Review changed files, Contract scope, Summary claims,
required jobs, Head SHA, and hosted logs. Local success is not hosted success.

Human decision: merge manually only when review and required hosted checks
pass. Do not enable automatic merge or provider branch deletion.

On GitHub, open the configuration PR's **Files changed** tab for the diff,
**Conversation** for reviewer decisions, and **Checks** for required jobs and
logs. The Head SHA shown by the PR must match the commit in the evidence.
Copy to the agent:

```text
Explain this configuration PR read-only. Map every changed file to Contract
scope and Summary evidence. List required GitHub jobs, their final state and
Head SHA, and open failures without hiding skipped jobs. Tell me PASS or STOP
for human merge review. Do not merge or delete the branch.
```

<!-- novice-stage: merge-and-close -->
## 13. Merge and close the lifecycle

After a human merges the configuration PR, separately approve
`make ai-close-work-item TASK=configure_ai_cockpit`.
Closure verifies archived evidence and PR ownership, synchronizes the base
fast-forward-only, deletes the remote/local work branch, checks a clean
worktree, and confirms local base equals remote base. Any failure is not
“closed.”

<!-- lifecycle-approval: configuration-closure-plan -->
**A. Review only.** Copy:

```text
The human has merged the configure_ai_cockpit PR. Verify the PR and archive
ownership, merged commit, exact closure command, affected branch, and every
validation. Change nothing and stop for my decision.
```

PASS: PR/archive/commit/branch/plan all agree. STOP: mismatch; contact the
repository owner with the evidence.

<!-- lifecycle-approval: configuration-closure-execute -->
**B. Approve closure only.** Copy:

```text
I approve lifecycle closure only for configure_ai_cockpit using the reviewed
plan. Run ai-close-work-item, verify remote/local configuration branch
deletion, clean worktree, fast-forward-only synchronization, and equality with
the remote default branch. Show every result and stop. On failure preserve the
branch/evidence and contact the repository owner. Do not start another Work
Item.
```

<!-- novice-stage: recover-from-a-stop -->
## 14. Recover from a stop

| Stop reason | Safe response |
| --- | --- |
| Dirty worktree | Identify and preserve every user change; use a separate branch/worktree or finish that work first. |
| No initial commit | Ask the repository owner to create/review the initial commit before adoption. |
| Missing tool | Install it through the organization's approved method; rerun read-only discovery. |
| Unknown default branch/remote | Inspect provider and Git remote HEAD; do not guess. |
| Active Work Item | Finish/close it or explicitly resume it; do not create a competing active item. |
| Managed-file conflict | Show a three-way explanation; preserve adopter content and revise the plan. |
| Calibration Unknown | Gather evidence or assign an owner; do not activate. |
| Local/hosted check failure | Preserve logs, diagnose root cause, update evidence, and rerun the same check. |
| PR merged but closure fails | Keep the branch, inspect closure evidence, and fix lifecycle state before reporting completion. |

<!-- novice-stage: confirm-installation-success -->
## 15. Final success checklist

Installation is complete only when all are true:

- the published fixed release and fetched base are recorded;
- the adoption and configuration Work Items each used a dedicated branch and
  reviewable lifecycle;
- every scaffold path and conflict was explained;
- all ten calibration stages and Unknowns were reviewed;
- quality commands came from project evidence and passed as recorded;
- the PR and required hosted jobs passed for the correct Head SHA;
- a human reviewed and merged;
- lifecycle closure deleted both work branches and synchronized the base;
- Cockpit Status matches archived evidence;
- residual platform/security/enterprise limits remain explicit.

If one item is false, describe the current stage as incomplete—do not call the
installation successful.

## Reference

- [Standard Adoption Guide](standard-adoption-guide.md)
- [Calibration Session](../reference/calibration-session.md)
- [Adopter Configuration](adopter-configuration.md)
- [Security and Release Verification](security-release-verification.md)
- [Documentation Architecture](../reference/documentation-architecture.md)
- [Upgrade](../reference/upgrade.md)
