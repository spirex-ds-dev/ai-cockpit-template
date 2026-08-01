---
author: Ray
title: "WI08 Interactive Installer UX Implementation Plan"
description: "TDD plan for converging the installer wizard on the required ten-stage operator flow."
audience: maintainers
status: current
authority: supporting
lastVerifiedBy: wi-08-interactive-installer-ux
---

# WI08 Interactive Installer UX Implementation Plan

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing safe installer wizard into the specified ten-stage, multilingual operator flow without adding a second write engine or activating calibration policy.

**Architecture:** `ai_installer_evidence` summarizes a dry-run Installer action list. `ai_install_plan` owns the immutable ten-stage representation, while `ai_install_wizard` owns selections, localized rendering, fail-closed stops, and delegation to the existing `Installer` transaction. The shell entrypoint and Installer transaction remain unchanged.

**Tech Stack:** Python 3.11+, dataclasses, standard-library I/O redirection, pytest, POSIX shell entrypoint tests, JSON locale resources.

## Global Constraints

- The existing `install_ai_cockpit.Installer` remains the sole write and rollback authority.
- No target write, branch creation, or branch switch may occur before affirmative confirmation.
- Standard is the display default; Strict is never auto-selected or activated.
- Installation never claims calibration or production readiness is complete.
- The wizard never commits, pushes, creates a PR, merges, or deletes a successful installation branch.
- English, Japanese, and Simplified Chinese locale files must retain exact key parity.

---

### Task 1: Deterministic planned-change summary

**Files:**
- Modify: `scripts/ai_installer_evidence.py`
- Create: `tests/test_installer_evidence.py`

**Interfaces:**
- Consumes: `Sequence[TransactionAction]` and the target `Path`.
- Produces: `InstallationPreview(adds, modifies, skips, source_code_changes, branch)` and `summarize_installation_actions(actions, *, target, branch)`.

- [ ] **Step 1: Write failing classification tests**

```python
def test_summarize_installation_actions_classifies_add_modify_and_skip(tmp_path):
    existing = tmp_path / "Makefile"
    existing.write_text("all:\n", encoding="utf-8")
    preview = summarize_installation_actions(
        [
            TransactionAction("write", tmp_path / "Makefile.ai", "new"),
            TransactionAction("append", existing, "include"),
            TransactionAction("skip", tmp_path / ".gitignore", "present"),
        ],
        target=tmp_path,
        branch="adopt/ai-cockpit",
    )
    assert (preview.adds, preview.modifies, preview.skips) == (1, 1, 1)
    assert preview.source_code_changes is False
```

- [ ] **Step 2: Run the new test and confirm it fails because the interface is absent**

Run: `.venv/bin/pytest -q tests/test_installer_evidence.py`

- [ ] **Step 3: Implement the immutable preview and conservative product-source classifier**

```python
@dataclass(frozen=True)
class InstallationPreview:
    adds: int
    modifies: int
    skips: int
    source_code_changes: bool
    branch: str

def summarize_installation_actions(actions, *, target: Path, branch: str) -> InstallationPreview:
    # Existing destinations are modifications; absent destinations are adds.
    # Known AI Cockpit managed paths are governance changes, not product source.
```

- [ ] **Step 4: Run the focused evidence tests**

Run: `.venv/bin/pytest -q tests/test_installer_evidence.py`

### Task 2: Ten-stage immutable plan

**Files:**
- Modify: `scripts/ai_install_plan.py`
- Modify: `tests/test_install_plan.py`

**Interfaces:**
- Consumes: `InstallationDetection`, `InstallationPreview`, selected mode, profile, stack, options, and branch.
- Produces: `WizardPlan.profile`, `WizardPlan.preview`, and exactly ten `STEP_NAMES` in the directive order.

- [ ] **Step 1: Replace the eight-stage assertion with the exact ten-stage contract**

```python
assert plan.step_names == (
    "Target Repository", "Readiness", "Installation Mode",
    "Governance Profile", "Planned Changes", "Conflict Review",
    "Explicit Confirmation", "Installation", "Verification", "Next Action",
)
assert plan.profile == "standard"
assert plan.steps[4].facts["adds"] == 41
```

- [ ] **Step 2: Run the focused plan test and confirm the eight-stage implementation fails**

Run: `.venv/bin/pytest -q tests/test_install_plan.py`

- [ ] **Step 3: Implement the ten stages with plan-only profile and preview facts**

```python
def build_wizard_plan(
    detection: InstallationDetection,
    *, stack: str, options: Mapping[str, object], branch: str,
    profile: str, preview: InstallationPreview,
) -> WizardPlan:
    steps = tuple(_step(name, facts={}) for name in STEP_NAMES)
    return WizardPlan(
        steps=steps,
        mode=detection.mode,
        stack=stack,
        options=dict(options),
        branch=branch,
        profile=profile,
        preview=preview,
    )
```

The Verification and Next Action steps must explicitly state that calibration
is separate and that no commit, push, PR, merge, or successful-branch deletion
occurs.

- [ ] **Step 4: Run the plan tests**

Run: `.venv/bin/pytest -q tests/test_install_plan.py tests/test_installer_evidence.py`

### Task 3: Interactive orchestration and localization

**Files:**
- Modify: `scripts/ai_install_wizard.py`
- Modify: `locales/wizard/en.json`
- Modify: `locales/wizard/ja.json`
- Modify: `locales/wizard/zh-CN.json`
- Modify: `tests/test_install_wizard.py`
- Modify: `tests/test_install_entrypoint.py`

**Interfaces:**
- Consumes: existing `collect_installation_detection`, `select`, `confirm`, and Installer factory.
- Produces: two explicit selections, read-only preview execution, ten-stage rendering, and localized result/next-action chrome.

- [ ] **Step 1: Add failing tests for the new input and stop paths**

```python
def test_dry_run_reports_ten_stages_and_standard_default(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    result = run_wizard(
        target=target,
        source=ROOT,
        language="en",
        input_fn=iter(["3", ""]).__next__,
        output=lambda _text: None,
        is_tty=True,
    )
    assert result.plan.profile == "standard"
    assert len(result.plan.steps) == 10

def test_blocked_conflict_review_never_invokes_write_installer(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    detection = collect_installation_detection(
        target, mode="new_adoption", stacks=("generic",)
    )
    calls = []
    monkeypatch.setattr(
        ai_install_wizard,
        "collect_installation_detection",
        lambda *args, **kwargs: replace(
            detection,
            readiness="blocked",
            blocking_reasons=("conflicts",),
        ),
    )
    result = run_wizard(
        target=target,
        source=ROOT,
        input_fn=iter(["1", "2"]).__next__,
        installer_factory=lambda **kwargs: calls.append(kwargs),
    )
    assert result.status == "blocked"
    assert calls == []
```

Add success and failure tests that assert Verification and Next Action output,
plus the existing entrypoint no-write assertions.

- [ ] **Step 2: Run the wizard tests and confirm they fail against the eight-stage flow**

Run: `.venv/bin/pytest -q tests/test_install_wizard.py tests/test_install_entrypoint.py`

- [ ] **Step 3: Add profile prompts and preview orchestration**

```python
PROFILE_LEVELS = ("lite", "standard", "strict")

def _preview_installer(*, installer_factory, installer_kwargs, target, branch):
    # Invoke Installer with dry_run=True under redirected stdout/stderr.
    # Return its action summary without target writes.
    preview = installer_factory(**{**installer_kwargs, "dry_run": True})
    exit_code = int(preview.install())
    if exit_code != 0:
        raise RuntimeError("installation preview failed")
    return summarize_installation_actions(preview.actions, target=target, branch=branch)
```

Blank profile input selects Standard; numbered input selects Lite, Standard, or
Strict. The selected value is never passed as an activation flag. Any preview
failure, blocked readiness, or conflict stops before write-Installer creation.

- [ ] **Step 4: Update all three locale files with exact-parity keys**

Add installation title, profile prompt/options, preview failure, verification,
and next-action strings; change the step heading denominator from 8 to 10.

- [ ] **Step 5: Run focused wizard, locale, and entrypoint tests**

Run: `.venv/bin/pytest -q tests/test_install_wizard.py tests/test_install_entrypoint.py tests/test_wizard_localization.py tests/test_install_plan.py tests/test_installer_evidence.py`

### Task 4: Public truth and governed verification

**Files:**
- Modify: `docs/architecture/interactive-installation-wizard.md`
- Modify: `docs/getting-started/installation.md`
- Modify: `docs/getting-started/installation.ja.md`
- Modify: `docs/getting-started/installation.zh-CN.md`
- Modify: `docs/reference/capability-truth-matrix.json`
- Modify generated capability and pre-release projections only when their validators require regeneration.
- Modify: `.ai/work-items/active/wi-08-interactive-installer-ux.summary.json`

**Interfaces:**
- Consumes: executable ten-stage behavior and focused test evidence.
- Produces: public documentation and capability claims bounded to observed behavior.

- [ ] **Step 1: Update architecture and installation routes**

Document the ten stages, Standard display default, plan-only profile, no-write
boundary, separate calibration, existing atomic rollback, and prohibited
automation.

- [ ] **Step 2: Refresh capability truth evidence and derived projections**

Run the repository-provided capability and documentation generators/checkers;
do not hand-edit generated digests or status files.

- [ ] **Step 3: Run the smallest relevant verification set**

Run: `.venv/bin/pytest -q tests/test_installer_evidence.py tests/test_install_plan.py tests/test_install_wizard.py tests/test_install_entrypoint.py tests/test_installer.py tests/test_adoption_e2e.py tests/test_wizard_localization.py`

Run: `make check-docs-metadata`, `.venv/bin/python scripts/ai_capability_truth.py`, and
`.venv/bin/python scripts/check_pre_release_documentation_alignment.py`.

- [ ] **Step 4: Complete Summary evidence and lifecycle verification**

Record scenario evidence, guideline compliance, observed issues, residual risk,
documentation alignment, and the exact focused commands. Then run the Contract
checks, `ai-finish`, archive, aggregate PR check, push, hosted checks, merge, and
`ai-close-work-item` in the canonical repository order.
