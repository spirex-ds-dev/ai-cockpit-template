"""Build the operator-facing eight-step Installation Wizard plan."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ai_installer_detection import InstallationDetection
from ai_installer_evidence import InstallationPreview

STEP_NAMES = (
    "Target Repository",
    "Readiness",
    "Installation Mode",
    "Governance Profile",
    "Planned Changes",
    "Conflict Review",
    "Explicit Confirmation",
    "Installation",
    "Verification",
    "Next Action",
)


@dataclass(frozen=True)
class WizardStep:
    """One explanatory wizard step; it has no side effects."""

    name: str
    purpose: str
    why: str
    facts: dict[str, object]
    suggested_value: str
    option_impact: str
    example: str
    write_status: str
    expected_result: str
    stop_condition: str
    checklist: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["suggestedValue"] = data.pop("suggested_value")
        data["optionImpact"] = data.pop("option_impact")
        data["writeStatus"] = data.pop("write_status")
        data["expectedResult"] = data.pop("expected_result")
        data["stopCondition"] = data.pop("stop_condition")
        data["checklist"] = list(self.checklist)
        return data


@dataclass(frozen=True)
class WizardPlan:
    """Complete immutable plan shown before confirmation."""

    steps: tuple[WizardStep, ...]
    mode: str
    stack: str
    options: dict[str, object]
    branch: str
    profile: str
    preview: InstallationPreview

    @property
    def step_names(self) -> tuple[str, ...]:
        return tuple(step.name for step in self.steps)

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "mode": self.mode,
            "stack": self.stack,
            "options": dict(self.options),
            "branch": self.branch,
            "profile": self.profile,
            "preview": {
                "adds": self.preview.adds,
                "modifies": self.preview.modifies,
                "skips": self.preview.skips,
                "sourceCodeChanges": self.preview.source_code_changes,
                "branch": self.preview.branch,
            },
        }


def _step(
    name: str,
    *,
    purpose: str,
    why: str,
    facts: dict[str, object],
    suggested: str,
    impact: str,
    example: str,
    expected: str,
    stop: str,
    checklist: tuple[str, ...],
) -> WizardStep:
    return WizardStep(
        name=name,
        purpose=purpose,
        why=why,
        facts=facts,
        suggested_value=suggested,
        option_impact=impact,
        example=example,
        write_status="read-only until final confirmation",
        expected_result=expected,
        stop_condition=stop,
        checklist=checklist,
    )


def build_wizard_plan(
    detection: InstallationDetection,
    *,
    stack: str,
    options: Mapping[str, object],
    branch: str,
    profile: str,
    preview: InstallationPreview,
) -> WizardPlan:
    """Create exactly ten deterministic stages from read-only detection facts."""
    if profile not in {"lite", "standard", "strict"}:
        raise ValueError("profile must be lite, standard, or strict")
    facts = detection.facts.to_dict()
    facts.update({"mode": detection.mode, "stacks": list(detection.stacks)})
    common_stop = (
        "Stop without writing when facts are blocked, unknown, or confirmation is not affirmative."
    )
    steps = (
        _step(
            STEP_NAMES[0],
            purpose="Identify the target repository.",
            why="All later choices depend on the exact root and remote.",
            facts=facts,
            suggested=str(facts["root"]),
            impact="Wrong target is a hard stop.",
            example="/Users/example/project",
            expected="The operator can verify root, branch, remote, and commit.",
            stop=common_stop,
            checklist=("root exists", "remote and default branch reviewed"),
        ),
        _step(
            STEP_NAMES[1],
            purpose="Explain repository readiness.",
            why="Readiness prevents unsafe adoption or upgrade writes.",
            facts={
                "clean": facts["clean"],
                "conflicts": facts["conflicts"],
                "activeWorkItems": facts["activeWorkItems"],
                "symlinkRisks": facts["symlinkRisks"],
                "missingTools": list(detection.missing_tools),
            },
            suggested=detection.readiness,
            impact=detection.plan.impact,
            example="clean=true, conflicts=[]",
            expected="Blockers and impact are visible before any write.",
            stop=common_stop,
            checklist=("worktree clean", "conflicts reviewed", "required tools present"),
        ),
        _step(
            STEP_NAMES[2],
            purpose="Choose New Adoption, Upgrade, or Dry Run.",
            why="Mode determines whether a transaction can be proposed.",
            facts={"mode": detection.mode},
            suggested=detection.mode,
            impact="Upgrade may require conflict review; Dry Run remains read-only.",
            example="new_adoption",
            expected="One explicit mode is recorded.",
            stop=common_stop,
            checklist=("mode selected", "mode impact understood"),
        ),
        _step(
            STEP_NAMES[3],
            purpose="Choose the governance profile to plan for later calibration.",
            why="The operator needs a visible governance intent without activating policy.",
            facts={"selected": profile, "available": ["lite", "standard", "strict"]},
            suggested="standard",
            impact="The selection is plan-only; Strict is never activated by installation.",
            example="standard",
            expected="One profile intent is visible while calibration remains separate.",
            stop=common_stop,
            checklist=("profile impact reviewed", "no automatic policy activation"),
        ),
        _step(
            STEP_NAMES[4],
            purpose="Review the exact planned change summary.",
            why="File impact and branch ownership must be visible before confirmation.",
            facts={
                "adds": preview.adds,
                "modifies": preview.modifies,
                "skips": preview.skips,
                "sourceCodeChanges": preview.source_code_changes,
                "branch": preview.branch,
            },
            suggested="review all counts",
            impact="Only AI Cockpit governance surfaces should change.",
            example="adds=41, modifies=1, sourceCodeChanges=false",
            expected="Adds, modifications, skips, source impact, and branch are explicit.",
            stop=common_stop,
            checklist=("counts reviewed", "source impact reviewed", "branch reviewed"),
        ),
        _step(
            STEP_NAMES[5],
            purpose="Review repository and managed-file conflicts.",
            why="Unresolved conflicts must stop before the write transaction.",
            facts={
                "conflicts": facts["conflicts"],
                "trackedHygiene": facts["trackedHygiene"],
                "symlinkRisks": facts["symlinkRisks"],
                "blockingReasons": list(detection.blocking_reasons),
            },
            suggested="continue only when empty",
            impact="Any blocker keeps the installer read-only.",
            example="conflicts=[]",
            expected="Every blocking conflict is explicit before confirmation.",
            stop=common_stop,
            checklist=("conflicts empty", "symlink risks empty", "hygiene reviewed"),
        ),
        _step(
            STEP_NAMES[6],
            purpose="Require an explicit affirmative installation decision.",
            why="A default or ambiguous response cannot authorize repository writes.",
            facts={
                "writeBoundary": "none_before_confirmation",
                "automation": "no commit / no push / no PR / no merge / no branch deletion",
                "profileActivation": "none",
            },
            suggested="decline unless the complete plan is understood",
            impact=detection.plan.impact,
            example="confirm: yes",
            expected="Only an explicit yes may invoke the Installer transaction.",
            stop=common_stop,
            checklist=detection.plan.checklist,
        ),
        _step(
            STEP_NAMES[7],
            purpose="Delegate the confirmed transaction to the existing Installer.",
            why="One transaction authority preserves atomic rollback and managed ownership.",
            facts={
                "mode": detection.mode,
                "stack": stack,
                "options": dict(options),
                "branch": branch,
                "transactionAuthority": "install_ai_cockpit.Installer",
            },
            suggested="execute only after confirmation",
            impact="Installer owns writes, backups, branch restoration, and rollback.",
            example="Installer.install()",
            expected="The transaction returns one observable exit code.",
            stop=common_stop,
            checklist=("single transaction authority", "no external automation"),
        ),
        _step(
            STEP_NAMES[8],
            purpose="Verify the observable installation result.",
            why="Installation success and rollback failure must not be conflated.",
            facts={"installerExitCode": "pending", "calibrationComplete": False},
            suggested="require exit code 0 for installation success",
            impact="A non-zero result is failed and must not claim successful recovery.",
            example="status=installed, exitCode=0",
            expected="Status and exit code are reported without a calibration claim.",
            stop=common_stop,
            checklist=("exit code recorded", "calibration not claimed"),
        ),
        _step(
            STEP_NAMES[9],
            purpose="Show the next bounded operator action.",
            why="Installation creates reviewable governance changes, not production readiness.",
            facts={
                "commit": False,
                "push": False,
                "pullRequest": False,
                "merge": False,
                "calibration": "separate workflow",
            },
            suggested="review the generated Work Item before any Git publication",
            impact="The successful installation branch remains for human review.",
            example="make ai-finish TASK=adopt_ai_cockpit REPORT_LANGUAGE=<conversation-locale>",
            expected="The next action is reviewable and calibration remains separate.",
            stop=common_stop,
            checklist=("review Work Item", "calibrate separately", "retain branch"),
        ),
    )
    return WizardPlan(
        steps=steps,
        mode=detection.mode,
        stack=stack,
        options=dict(options),
        branch=branch,
        profile=profile,
        preview=preview,
    )
