---
author: Ray
title: "AI Cockpit"
description: Application-language-agnostic collaborative engineering environment and AI governance template for Codex, Gemini, Claude, Cursor, Antigravity, and other agentic coding tools.
keywords:
  - ai-agents
  - ai-agent
  - ai-workflow
  - code-review
  - llmops
  - ai-safety
  - codex
  - gemini
  - claude
  - cursor
  - antigravity
  - agentic-coding
  - developer-tools
  - developer-workflow
  - governance
  - template
  - automation
  - ci
---

# AI Cockpit

For quality-gate ownership, timing evidence, and the required Work Item
traceability lifecycle, see [Quality Gate Operations](docs/operations/quality-gates.md).

Current adoption guidance is layered: [30-Second Start](docs/getting-started/30-second-start.md), [Standard Adoption Guide](docs/getting-started/standard-adoption-guide.md), and [Security and Release Verification](docs/getting-started/security-release-verification.md). Historical plans and archived records are evidence context, not current instructions.

[中文](README.zh-CN.md) | [日本語](README.ja.md)

AI coding agents can:

- rewrite unrelated files
- silently remove tests
- bypass verification
- leave reviewers guessing

AI-generated changes should not be accepted without bounded, independently enforced review. The practical question is not whether humans should trust agents more, but when the available evidence supports reliance, investigation, intervention, or a stop.

**AI Cockpit enables calibrated trust between humans and AI agents through evidence-based governance.**

Calibrated trust does not mean maximizing trust in an agent. It means enabling humans to rely on the agent when evidence supports reliance and to intervene when evidence is missing, stale, contradictory, or insufficient.

AI Cockpit is a repository governance layer, not an agent runtime or security sandbox. Its deterministic gates cover declared, externally reviewable known-risk cases; they do not classify every semantic danger or prove agent intent. Runtime installation is not calibration completion: the current `configure_ai_cockpit` flow produces and validates a Project Profile proposal, while the resumable ten-stage session and Candidate activation are implemented Runtime capabilities that still require adopter execution and human confirmation. Updates require Impact Assessment before recalibration. See the [Capability Truth Matrix](docs/reference/capability-truth-matrix.md) for evidence boundaries.

## Why AI Cockpit exists

AI Cockpit is not a business skill or an agent runtime. It is a Human-Agent Trust Layer that uses reviewable evidence to determine when an agent may continue, when a human must decide, and when the governed path must stop. Read [Human-Agent Trust Layer](docs/trust-layer.md).

## Interactive entrypoints

Use `./install.sh` with a TTY and no arguments, or pass `--interactive`, for the eight-step Installation Wizard. It detects the target repository, accepts one numeric mode input (`1` New Adoption, `2` Upgrade, `3` Dry Run), shows the complete write plan, and waits for explicit confirmation before writing. The current low-level selector does not render those labels itself, so the prompt-first Installation guide supplies the mapping and review context. Non-interactive no-argument use fails closed; explicit legacy flags keep their deterministic behavior. The wizard never commits, pushes, opens a PR, or merges.

After installation, the agent uses the installed `make cockpit-calibrate-session ARGS="..."` interface for the resumable ten-stage Calibration Session. It supports Back/Pause/Resume and stale revalidation, blocks on Unknown or stale evidence, and requires separate Reviewer and Owner confirmations before atomic Candidate activation. The friendlier `make cockpit-calibration-wizard` command is template-maintenance-only and is not installed into adopter projects. The persisted Session schema currently records Japanese as its language; this does not claim that every visible string is localized.

The mobile examples are evidence fixtures and documented scenarios. Hosted verification currently covers a minimal Swift Package and Android smoke paths; Xcode projects/workspaces, CocoaPods, project-specific Gradle variants, host JDK selection, and instrumented execution require adopter calibration and are not implied by the wizard.

## What is AI Cockpit?

**AI Cockpit is a Repository Governance Layer for AI-assisted Software Development.** This is the concrete product boundary through which its mission is delivered.

It is **not** an Agent Runtime, **not** a Workflow Engine, and **not** a Security Sandbox.

This boundary is canonical across the English, Chinese, and Japanese guides: repository-local records support review, but trusted identity, production isolation, enterprise audit/compliance, and provider-hosted release evidence remain external controls.

See the [enterprise control checklist](docs/reference/enterprise-control-checklist.md) and its [machine-readable status matrix](docs/reference/enterprise-control-matrix.json). These do not claim external verification; the mandatory Japanese capability gate remains WI-16 before publication.

Its philosophy is **Evidence over Self-Declaration**. Its mechanism is **Evidence Governance**: AI Cockpit creates governance records, evaluates delegated evidence, and compresses both into human decision state.

It provides:

- **Governance**: Scope boundaries, verification requirements, policy enforcement
- **Repository Context**: Explicit intent, constraints, architectural knowledge
- **Verification**: Independent validation of changes against declared contracts
- **Auditability**: Complete records of what changed, why, and how it was verified
- **Intent**: First-class representation of why work exists, not just what to implement

AI Cockpit does not replace agents like Claude Code, Codex, Cursor, or Gemini CLI. Agents evolve continuously with model capabilities. **Governance should remain stable.**

AI Cockpit checks diffs after writes; it is not a filesystem permission boundary or security sandbox.

Its known-risk guards provide deterministic coverage for declared dangerous patterns and fail closed when evidence is missing or contradictory; finite regression tests are not universal semantic-risk detection. Work Items follow the governed lifecycle: latest remote base → dedicated branch → Contract/Preflight → implementation and checks → Summary/archive → push → PR → merge → `make ai-close-work-item` → synchronized clean base and branch cleanup. Release evidence remains separate from repository-local governance evidence.

AI Cockpit governs evidence; it does not replace evidence-producing tools. The Native Governance Evidence / Delegated Domain Evidence model and release boundary are defined in [Design Philosophy](docs/philosophy/design-philosophy.md).

![AI Cockpit demo](docs/assets/ai-cockpit-demo.gif)

**AI changed 37 files. Cockpit stopped the merge.**

AI Cockpit makes AI-generated changes bounded, reviewable, and auditable.

I kept seeing AI rewrite unrelated files, roll back completed work, and bypass review expectations. So I built a governance layer around scope, checks, summaries, and status, with explicit contracts as the core control mechanism.

## 30-Second Version

Before:

```text
AI changed 24 files.
Nobody knows why.
Tests may have disappeared.
Review starts from confusion.
```

After:

```text
Task scope declared.
Checks enforced.
Summary generated.
Cockpit updated.
Review starts from context.
```

Version history and capability evolution are maintained in the [Roadmap](docs/roadmap.md), not in this short entry page.

<!-- install-prerequisites: python3.11,git-initial-commit,curl,gnu-make,posix -->

**Prerequisites:** Linux, macOS, or WSL with a POSIX shell; Python 3.11+; Git, curl, and GNU Make; and a clean Git repository with at least one commit. The selected stack's formatter, test runner, SDK, and build plugins must already be installed.

## Quick Install

Use this when you want the shortest path to a fresh adoption install. For the full lifecycle and page map, read [Installation](docs/getting-started/installation.md), [Adopter Configuration](docs/getting-started/adopter-configuration.md), and [Documentation Architecture](docs/reference/documentation-architecture.md).
The quick-install flow resolves the documented release metadata from the public release source first. `AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY` and `AI_COCKPIT_TEMPLATE_RAW_BASE` are used only to resolve the release tag and fetch the installer; the installer itself still honors `AI_COCKPIT_TEMPLATE_REPO` and `AI_COCKPIT_TEMPLATE_SOURCE` for its own clone or source selection. If your repository or release artifacts are private, use a local clone or configured source instead of relying on the quick-install bootstrap path.

Beginner route—paste this into the agent with your project open:

```text
Follow the complete English Installation guide for this project. Begin with
read-only prerequisites and discovery. Explain every term and use the
canonical fixed public release unless I provide a verified private mirror.
At every step show evidence, expected result, PASS/STOP, and who to contact.
Ask for a separate decision before write, commit, push, PR preparation, human
merge, lifecycle closure, and configuration. Never run later steps from one
continuous shell block.
```

The block below is an **advanced manual fallback**, not the beginner route.
Run only through local finish/archive, then stop:

<!-- command-evidence: adopter_required -->
```sh
STACK="${STACK:-generic}" # generic, python, go, rust, typescript, java, android, kotlin, flutter, swift, ruby, php, or csharp
PUBLIC_REPOSITORY="${AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY:-https://github.com/spirex-ds-dev/ai-cockpit-template.git}"
RAW_BASE="${AI_COCKPIT_TEMPLATE_RAW_BASE:-https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template}"
RELEASE_TAG="$(curl -fsSL "${RAW_BASE}/main/release.json" | python3 -c 'import json,sys; value=json.load(sys.stdin)["releaseTag"]; assert isinstance(value,str) and value; print(value)')"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
curl -fsSL "${RAW_BASE}/${RELEASE_TAG}/install.sh" -o "$INSTALLER"
AI_COCKPIT_TEMPLATE_REPO="$PUBLIC_REPOSITORY" \
  AI_COCKPIT_TEMPLATE_REF="$RELEASE_TAG" sh "$INSTALLER" --stack "$STACK" --update-makefile --create-adoption
make ai-finish TASK=adopt_ai_cockpit
```

Stop and review the archive/diff. After separate human commit approval:

<!-- command-evidence: adopter_required -->
```sh
ADOPTION_CONTRACT="$(python3 -c 'import json; entries=[item for item in json.load(open(".ai/work-items/archive/index.json"))["entries"] if item["workItemId"]=="adopt_ai_cockpit"]; assert len(entries)==1; print(entries[0]["contractPath"])')"
ADOPTION_BASE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["baseCommit"])' "$ADOPTION_CONTRACT")"
git add .
git commit -m "adopt AI Cockpit governance"
make check-ai-pr AI_BASE_COMMIT="$ADOPTION_BASE"
```

Stop. Obtain push approval, open the PR, pass hosted CI, and have a human
merge. Only after separate lifecycle-closure approval run:

<!-- command-evidence: adopter_required -->
```sh
make ai-close-work-item TASK=adopt_ai_cockpit
```

Only after closure synchronizes the default branch, separately begin
configuration:

<!-- command-evidence: adopter_required -->
```sh
CONFIG_BASE="$(git rev-parse HEAD)"
make ai-start TASK=configure_ai_cockpit TITLE="Configure AI Cockpit for this project" MODE=code
```

For adopter repositories, stop after local finish/archive and obtain explicit human approval before `git commit`, then a separate approval before `git push`. PR creation may prepare review, but PR merge must be manual. After manual merge, obtain explicit approval before `make ai-close-work-item TASK=<task>`; do not enable automatic merge or branch deletion. This conservative gate applies to installation and upgrade in adopter projects only; the template repository keeps its own maintenance workflow.

The command requires the authoritative public `release.json` projection and then downloads only that fixed tag's installer. It stops if the projection is unavailable or invalid; it never guesses from the highest tag. Before treating the projection as a verified public release, also require a stable (not draft) provider Release, matching tag-pinned metadata and source commit, a downloadable installer and archive asset, and matching digests. A tag or repository `release.json` alone is not provider publication evidence.

Review and extend the generated configuration Contract scope before changing Project Profile, Guard, quality-command, or CI files. Then calibrate the installed runtime before enabling blocking gates:

<!-- governance-flow: install,configure-work-item,onboard,doctor,calibrate,confirm,validate,readiness,develop -->

```sh
make ai-onboard
# Or step by step:
make cockpit-doctor
make cockpit-calibrate
# Review .ai/project_profile.proposed.yaml, then create and approve .ai/project_profile.yaml.
make check-ai-project-profile
make check-ai-guard-calibration
make check-ai-adoption-ready
make ai-finish TASK=configure_ai_cockpit
```

Stop and review the configuration archive/diff. After separate commit approval:

<!-- command-evidence: adopter_required -->
```sh
git add .
git commit -m "configure AI Cockpit for this project"
make check-ai-pr AI_BASE_COMMIT="$CONFIG_BASE"
```

Doctor records detected facts, evidence, confidence, suggestions, and unknowns without changing project policy. Calibration creates only a proposal; it never overwrites Guards or approves high-risk paths. After explicit human confirmation and successful readiness checks, start a governed task:

```sh
make ai-start TASK=example_change TITLE="Example change" MODE=code
```

Finish it with checks and an audit trail:

```sh
make ai-finish TASK=example_change
```

## How It Works

The governance loop:

```text
Intent → Contract → Implementation → Verification → Summary (Repository Truth) → Cockpit (Governance Compression) → Human Decision
```

| Layer | What it does |
| --- | --- |
| Intent | Declares why the work exists, constraints to respect, and rationale for the approach (optional but recommended). |
| Work Item Contract | Declares the task boundary before AI changes files. |
| Scope Guard | Detects changes outside the declared scope and blocks finish, archive, or merge gates. |
| Backtrack Guard | Detects protected test, snapshot, or Work Item record deletion and blocks configured gates. |
| Coverage Guard | Requires each configured production path to have a changed test path matched by a project-owned association rule; it does not inspect test contents or prove runtime coverage. |
| Scenario Coverage | Records generic risk-domain coverage for medium/high-risk Work Items using the policy in `.ai/guards/scenario_coverage_policy.yaml`. Scenario content stays in the Work Item. |
| Agent Risk Guard | Hard gate against prompt-is-advice, mid-task drift, and unknown-overclaim risks. |
| AI Review Policy | Flags governance and CI changes that need explicit review focus. |
| Checkpoint | Mid-task snapshot to detect scope drift before finishing. |
| Status Consistency Guard | Verifies Cockpit status matches the current set of active Work Items. |
| Change Summary | Records what changed, what was verified, what risk remains, whether intent was achieved, and any scenario coverage evidence. |
| Cockpit Status | Shows the current AI task state in one generated view, including the compressed scenario coverage signal. |
| Finish Flow | Archives the Work Item only after checks pass. |

## Core Principles

- **Intent-driven Development**: Work should be driven by declared intent (problem, constraints, rationale), not only by task descriptions
- **Evidence over Self-Declaration**: Readiness and trust decisions should be based on reviewable evidence, not agent confidence
- **Machine-verifiable contracts**: Governance depends on structured, auditable records
- **Minimal process**: Add governance only where it prevents real failures
- **Scope-first engineering**: Declare boundaries before changing files
- **Backward compatibility by default**: Schema evolution is conservative
- **Explicit non-goals**: Document what should not be solved in this scope
- **Prefer extending existing concepts**: Avoid inventing new abstractions prematurely
- **Documentation before schema**: Design principles are documented before implementation

See also: [Work Item Style Guide](docs/work-item-style-guide.md), [Roadmap (V1–V4)](docs/roadmap.md)

AI Cockpit stores evidence, not reasoning. Reasoning guides the agent; evidence supports review, verification, and audit. Only reviewable evidence belongs in repository records.

Every new schema field should answer one question: what machine-verifiable evidence does this field preserve?

## Responsibility Model

| Layer | Responsibility |
| --- | --- |
| Human Intent | Why the work exists |
| Agent Thinking | How the task is interpreted |
| Reviewable Evidence | What the repository records |
| Repository Governance | What checks and policies validate |
| Repository History | What is preserved for audit and review |

Thinking can be rich and contextual, but repository records should preserve reviewable evidence. Governance checks operate on that evidence, not on private reasoning.

## Review Lenses

| Review Lens | AI Cockpit Surface |
| --- | --- |
| Empathy | `problemStatement`, `intent.problem`, `intent.constraints`, `intent.rationale`, `sources` |
| Design | `acceptance`, `guidelines` |
| Architecture | `scope`, `outOfScope`, `riskAssessment`, `rollbackNote` |
| Implementation | `mode`, actual diff, `changedFiles` |
| Judgment | `unknowns`, `notCodable`, `agentCapability`, `executionDecision`, `reviewReadiness` |
| Shipping | `verification`, `Summary`, `Cockpit Status`, `Archive` |

These are review lenses, not hard lifecycle phases.
The lenses explain how to review and reason about a task, not how the repository records private reasoning.
They do not replace `Plan -> Scope -> Verify -> Summarize -> Status -> Archive`.

Do not add `workflowPhase`.
Do not add `workflowEvidence`.
Do not require empathy, design, architecture, implementation, judgment, or shipping fields.
Agents must not invent missing user impact or business motivation.
Prefer explicit `not provided` over inferred explanations.

## Trust Model

The Trust Layer makes this operational: continue only when repository and delegated-tool evidence supports the change; otherwise stop, request a human decision, or choose a narrower safe alternative. Agent explanations and self-declared approvals help explain a decision but never substitute for independently verifiable evidence. See the [Trust Layer guide](docs/trust-layer.md) and run the offline [failure demo](docs/examples/trust-layer-demo.sh).

- `ai-start` records `baseCommit` and fingerprints pre-existing dirty paths.
- Guards inspect committed changes from `baseCommit...HEAD` plus staged, unstaged, and untracked changes. CI can set `AI_BASE_COMMIT` to the PR merge-base.
- Contracts reference registered check IDs; they cannot supply executable command strings. Registered checks resolve through `.ai/cockpit/checks.yaml` to explicit Make targets.
- `ai-finish` records the resolved check ID, exit code, duration, timestamp, execution commit, Contract hash, normalized command hash, output digest, and redacted output summary.
- These fields are structured execution records, not cryptographic or tamper-proof attestations. CI revalidates every changed archive pair and the complete PR diff.
- CI also runs supply-chain evidence checks for the dev dependency lockfile, SBOM/provenance baselines, and secret scanning so release metadata drift is visible before publication.
- Restricted/destructive approval fields are self-declared workflow records. Trusted human approval must come from an external boundary such as CODEOWNERS review, a protected CI environment, or platform identity events.
- Active records stay local; successfully archived records are versionable audit artifacts under `.ai/work-items/archive/`.
- The installer ships the same PR validator and Make targets as the installed AI Cockpit runtime. CI runs `make check-ai-pr AI_BASE_COMMIT=<merge-base>` after Work Items are archived.
- Every non-exempt PR path must be both scoped and reported by the same archived Contract/Summary pair.

The generic stack intentionally fails `quality` until its formatter, test, and lint commands are configured. A no-op quality gate is not a gate.

Template contributors can install the regression-test dependency with `python3 -m pip install --require-hashes -r requirements-dev.lock`. Regenerate that file from the committed `requirements-dev.in` with `pip-compile --generate-hashes --allow-unsafe` when intentionally changing the toolchain. Runtime governance scripts still use only the Python standard library.

AI Cockpit reduces accidental scope drift and makes review evidence explicit; it is not a security sandbox for a malicious agent that can modify repository policy. For the public release selected above, run project tests or `make ai-cockpit-quality` as an independent required CI check in addition to `check-ai-pr`.

## What It Catches

```text
[BLOCKED]
Scope violation detected.

Unauthorized file modification:
- src/auth/payment.rs

Allowed scope:
- src/auth/session.rs
- tests/auth/session_test.rs
```

## Supported

Agents:

```text
Codex, Gemini, Claude, Cursor, Antigravity, and other coding agents
```

Stacks:

```text
generic, rust, flutter, typescript, python, go, java, android, kotlin, swift, ruby, php, csharp
```

Compatibility levels:

<!-- stack-tiers: verified=python,go,rust,typescript,java,kotlin,ruby,php,csharp,flutter,android,swift; workflow-implemented=; preset-only=generic -->

- **Hosted verification recorded:** `python`, `go`, `rust`, and `typescript` run minimal-project jobs in `real-stack-quality`. `java`, `kotlin`, `ruby`, `php`, and `csharp` run the same gate in `extended-real-stack-quality`. `flutter`, `android`, and `swift` run the same gate in `mobile-stack-quality`.
- **Swift verified scope:** `mobile-stack-quality` exercises a minimal Swift Package Manager fixture only. Hosted verification does **not** cover Xcode projects, workspaces, or CocoaPods; those layouts require Project Calibration after installation.
- **Beginner platform routes:** use the complete [Installation](docs/getting-started/installation.md), then follow the [iOS](docs/getting-started/examples/ios.md), [Android](docs/getting-started/examples/android.md), or [Java](docs/getting-started/examples/java.md) example. Finding platform project files identifies only a likely layout; it does not confirm that development tools, devices, signing credentials, or cloud CI work.
- **Preset only:** `generic` intentionally fails closed until its formatter, test, and lint commands are configured.
- **Unsupported runtime/platform:** native Windows shells. Use WSL or another POSIX environment.

Stack presets are calibration starting points, not dependency installers. Install the selected project's formatter, test runner, SDK, and build plugins first; for example, the Java and Android presets expect a Gradle wrapper and Spotless configuration, while Python expects Ruff and pytest. The examples directory covers selected stacks and does not include every preset.

The governance runtime is language-agnostic, but stack presets and default guard paths are not universal framework support. Review `Makefile.ai.stack` and `.ai/guards/coverage_policy.yaml` against the target repository before making them required CI gates.

Installation deploys the runtime; it does not complete production adaptation. The separate `configure_ai_cockpit` Work Item owns Project Profile, Guard, quality-command, and CI adaptation. Adoption readiness also requires an approved Project Profile, Profile/Guard consistency, non-placeholder quality commands, reviewed Coverage paths, and CI wiring for both `ai-cockpit-quality` and `check-ai-pr`. This is a static completeness check, not a security proof or proof that project commands are meaningful.

<!-- release-capabilities: auditable-adoption,sha256-verification -->
<!-- public-quality-target: ai-cockpit-quality -->

The public release contract includes auditable first-adoption bootstrap and strict Quick Install binding to the published tag, source commit, installer digest, and downloadable release-archive SHA256. Quick Install fails closed when any binding or archive asset is missing or mismatched; the caller-provided `AI_COCKPIT_TEMPLATE_SHA256` is only an additional assertion. Project-specific quality, Coverage paths, and CI still require explicit adaptation.

## Runtime Requirements

- Python 3.11 or higher.
- Git environment with support for merge-base and three-dot diffs (`...`).
- POSIX-compliant shell and GNU Make execution environment.
- Linux and macOS are officially supported for local execution and CI. Native Windows shells are not supported; please run inside WSL (Windows Subsystem for Linux) or another POSIX terminal.

Repository `make quality` runs the full test suite with an 85.10% overall script coverage floor and per-file regression floors for lifecycle-critical scripts, Ruff over `scripts/` and `tests/`, Mypy over all governance scripts, Bandit with an exact reviewed low-risk baseline and zero unregistered medium/high findings, Python compilation, diff checks, and documentation consistency.

## Advanced Docs

- [Installation](docs/getting-started/installation.md)
- [First Work Item](docs/getting-started/first-work-item.md)
- [Roadmap (V1–V4)](docs/roadmap.md)
- [Japanese Concept Guide](docs/overview.ja.md)
- [How to Read Cockpit Status](docs/reference/how-to-read-cockpit-status.md)
- [Concept Guide (Japanese)](docs/overview.ja.md)
- [Contract & Summary Fields Manual](docs/contract-fields.md)
- [Configuration](docs/configuration.md)
- [Non-Make Adaptation (Japanese)](docs/non-make-adaptation.ja.md)
- [Architecture](docs/architecture.md)
- [Documentation Architecture](docs/reference/documentation-architecture.md)
- [Design Philosophy](docs/philosophy/design-philosophy.md)
- [Case Study: Stopping AI Rollback Corruption](docs/case-study-ai-rollback-corruption.md)
- [Language Examples](examples/)
