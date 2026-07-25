"""Build the operator-facing eight-step Installation Wizard plan."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from ai_installer_detection import InstallationDetection


STEP_NAMES = (
    "Target Repository",
    "Repository Readiness",
    "Installation Mode",
    "Project Stack",
    "Installation Options",
    "Adoption Branch",
    "Installation Plan Review",
    "Installation/Result",
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
    detection: InstallationDetection, *, stack: str, options: Mapping[str, object], branch: str
) -> WizardPlan:
    """Create exactly eight deterministic steps from read-only detection facts."""
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
            purpose="Summarize detected project stacks.",
            why="Stack signals determine compatible installer options.",
            facts={"stacks": list(detection.stacks)},
            suggested=stack,
            impact="Multi-stack keeps all detected signals for review.",
            example="swift + android",
            expected="iOS, Android, Generic, or multi-stack facts are shown.",
            stop=common_stop,
            checklist=("stack signals reviewed", "multi-project layout checked"),
        ),
        _step(
            STEP_NAMES[4],
            purpose="Review installation options.",
            why="Options change files and conflict behavior after confirmation.",
            facts=dict(options),
            suggested="defaults",
            impact="Force and examples affect the eventual transaction.",
            example="force=false, with_examples=false",
            expected="Options are explicit and stable.",
            stop=common_stop,
            checklist=("force policy reviewed", "examples and Makefile options reviewed"),
        ),
        _step(
            STEP_NAMES[5],
            purpose="Review the adoption branch boundary.",
            why="Branch facts prevent accidental work on the wrong base.",
            facts={"branch": facts["branch"], "defaultBranch": facts["defaultBranch"]},
            suggested=branch,
            impact="Branch selection is passed to the existing transaction only after confirmation.",
            example="ai-cockpit/adopt",
            expected="Base remote and branch are visible.",
            stop=common_stop,
            checklist=("base branch reviewed", "no automatic push or merge"),
        ),
        _step(
            STEP_NAMES[6],
            purpose="Show the complete plan for final review.",
            why="The operator must see every fact, impact, and write boundary together.",
            facts=detection.plan.to_dict(),
            suggested="confirm after review",
            impact=detection.plan.impact,
            example="writeBoundary=none_before_confirmation",
            expected="The full eight-step plan is rendered before confirmation.",
            stop=common_stop,
            checklist=detection.plan.checklist,
        ),
        _step(
            STEP_NAMES[7],
            purpose="Report Dry Run or confirmed installation result.",
            why="The result must distinguish proposal, cancellation, and transaction output.",
            facts={
                "writeBoundary": "none_before_confirmation",
                "automation": "no commit / no push / no PR / no merge",
            },
            suggested="cancel unless confirmed",
            impact="Only affirmative confirmation can invoke Installer.",
            example="confirm: yes",
            expected="Result includes status and exit code.",
            stop=common_stop,
            checklist=("confirm explicitly", "preserve conflict files", "report result"),
        ),
    )
    return WizardPlan(
        steps=steps, mode=detection.mode, stack=stack, options=dict(options), branch=branch
    )
