"""Deterministic, fail-closed classification for untrusted instructions."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    HUMAN = "human"
    REPOSITORY = "repository"
    ISSUE = "issue"
    WEB = "web"
    LOG = "log"
    DEPENDENCY = "dependency"
    TOOL = "tool"
    GENERATED = "generated"


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class InstructionAuthority(str, Enum):
    HUMAN_REQUEST = "human_request"
    NONE = "none"


class InjectionOutcome(str, Enum):
    DETECTED = "detected"
    CONTAINED = "contained"
    BLOCKED = "blocked"
    HUMAN_CONFIRMATION_REQUIRED = "human_confirmation_required"
    NOT_DETECTED = "not_detected"
    OUT_OF_SCOPE = "out_of_scope"


class GovernanceDecision(str, Enum):
    """A reviewable decision; it never grants a high-risk operation."""

    ALLOW = "allow"
    REVIEW = "review"
    CONFIRM = "confirm"
    BLOCK = "block"


class GovernanceSignal(str, Enum):
    """Human-readable next-step signal derived from a governance decision."""

    ALLOW = "🟢"
    HUMAN_ACKNOWLEDGMENT_REQUIRED = "🟡"
    BLOCK = "🔴"


_INJECTION_PATTERNS = (
    r"administrator\s+approved",
    r"忽略策略|伪造管理员批准|跳过审查",
    r"管理者.{0,12}(?:承認|許可)|審査.{0,12}(?:無視|スキップ)|(?:秘密|トークン).{0,12}(?:表示|公開)",
    r"override\s+(?:approval|guard|policy)",
    r"(?:skip|bypass|disable)\s+(?:review|guard|policy)",
    r"(?:print|expose|reveal)\s+(?:the\s+)?(?:secret|token|key)",
    r"approve\s+(?:release|merge|push)",
    r"display\s*:\s*none",
    r"\u202e",
)
_DANGEROUS_TERMS = ("release", "merge", "push", "delete", "secret", "token", "批准")


@dataclass(frozen=True)
class InputTrustRecord:
    sourceType: str
    trustLevel: str
    instructionAuthority: str
    mayContainInstructions: bool
    external: dict[str, Any]
    outcome: str
    reason: str


@dataclass(frozen=True)
class HighRiskDecision:
    allowed: bool
    outcome: str
    reason: str


@dataclass(frozen=True)
class GovernanceRequest:
    """Facts supplied by a caller for a governed-request assessment.

    This is deliberately not an executor and does not discover repository
    references, reviewer identity, release state, or archive ownership.
    """

    sourceType: SourceType | str
    content: str
    requestedOperation: str
    riskCategory: str
    evidenceConflict: bool
    independentAuthorization: bool
    recovery: str


@dataclass(frozen=True)
class GovernanceAssessment:
    caseId: str
    sourceType: str
    trustLevel: str
    instructionAuthority: str
    requestedOperation: str
    evidenceConflict: bool
    coverageStatus: str
    decision: str
    gate: str
    reason: str
    missingEvidence: str
    recovery: str

    @property
    def signal(self) -> str:
        """Return the deterministic traffic-light next-step signal.

        Yellow covers both review and confirmation: neither authorizes an
        automatic next step. Red is a blocking decision, not a claim about a
        requester's intent.
        """

        if self.decision == GovernanceDecision.ALLOW.value:
            return GovernanceSignal.ALLOW.value
        if self.decision == GovernanceDecision.BLOCK.value:
            return GovernanceSignal.BLOCK.value
        return GovernanceSignal.HUMAN_ACKNOWLEDGMENT_REQUIRED.value

    @property
    def mayProceedAutomatically(self) -> bool:
        """Only an evidence-backed allow decision can advance automatically."""

        return self.decision == GovernanceDecision.ALLOW.value

    @property
    def refusal(self) -> dict[str, str | bool] | None:
        """Return the actionable record an agent must present before stopping.

        ``allow`` has no refusal record.  Every other decision is deliberately
        explicit so a caller cannot convert an evidence gap into implied
        permission or a vague request to "review".
        """

        if self.decision == GovernanceDecision.ALLOW.value:
            return None
        return {
            "signal": self.signal,
            "mayProceedAutomatically": self.mayProceedAutomatically,
            "decision": self.decision,
            "reason": self.reason,
            "missingEvidence": self.missingEvidence,
            "recovery": self.recovery,
        }


def _decode_base64(value: str) -> str:
    compact = re.sub(r"\s+", "", value)
    if len(compact) < 12 or len(compact) % 4:
        return ""
    try:
        decoded = base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error):
        return ""
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _matches(value: str) -> list[str]:
    lowered = value.casefold()
    matches = [pattern for pattern in _INJECTION_PATTERNS if re.search(pattern, lowered)]
    decoded = _decode_base64(value)
    if decoded and any(term in decoded.casefold() for term in ("approve", "release", "secret")):
        matches.append("base64-encoded-instruction")
    if decoded:
        matches.extend(_matches(decoded))
    return sorted(set(matches))


def assess_input(source_type: SourceType | str, content: str) -> InputTrustRecord:
    source = SourceType(source_type).value
    if not isinstance(content, str) or not content:
        return InputTrustRecord(
            source,
            TrustLevel.UNTRUSTED.value,
            InstructionAuthority.NONE.value,
            False,
            {},
            InjectionOutcome.OUT_OF_SCOPE.value,
            "empty or non-text input is outside classifier scope",
        )
    if source == SourceType.HUMAN.value:
        return InputTrustRecord(
            source,
            TrustLevel.TRUSTED.value,
            InstructionAuthority.HUMAN_REQUEST.value,
            True,
            {},
            InjectionOutcome.NOT_DETECTED.value,
            "human content is a candidate request, not automatic proof of approval",
        )
    matches = _matches(content)
    dangerous = any(term in content.casefold() for term in _DANGEROUS_TERMS)
    outcome = (
        InjectionOutcome.BLOCKED.value
        if dangerous and matches
        else (InjectionOutcome.DETECTED.value if matches else InjectionOutcome.CONTAINED.value)
    )
    reason = "embedded instruction remains content and cannot grant execution authority"
    if matches:
        reason += f"; indicators={','.join(matches)}"
    return InputTrustRecord(
        source,
        TrustLevel.UNTRUSTED.value,
        InstructionAuthority.NONE.value,
        True,
        {},
        outcome,
        reason,
    )


def re_evaluate_high_risk_operation(record: InputTrustRecord, operation: str) -> HighRiskDecision:
    if (
        record.sourceType != SourceType.HUMAN.value
        or record.instructionAuthority != InstructionAuthority.HUMAN_REQUEST.value
    ):
        return HighRiskDecision(
            False,
            InjectionOutcome.HUMAN_CONFIRMATION_REQUIRED.value,
            f"explicit human confirmation required before {operation}",
        )
    return HighRiskDecision(
        False,
        InjectionOutcome.HUMAN_CONFIRMATION_REQUIRED.value,
        f"policy re-evaluation required before {operation}",
    )


_CASE_ID_BY_RISK = {
    "destructive_change": "RAI-01",
    "external_instruction": "RAI-02",
    "evidence_destruction": "RAI-03",
    "forged_approval": "RAI-04",
    "untrusted_instruction_like_content": "RAI-05",
    "sensitive_data_exfiltration": "RAI-06",
    "evidence_hallucination": "RAI-07",
    "release_bypass": "RAI-08",
    "archive_immutability": "RAI-09",
    "unverified_execution": "RAI-10",
    "scope_bypass": "RAI-11",
    "separation_of_duties": "RAI-12",
}


def _assessment(
    request: GovernanceRequest,
    record: InputTrustRecord,
    coverage_status: str,
    decision: GovernanceDecision,
    gate: str,
    reason: str,
) -> GovernanceAssessment:
    missing_evidence = "none"
    if decision is not GovernanceDecision.ALLOW:
        if coverage_status == "not_covered":
            missing_evidence = (
                "the repository, lifecycle, or identity fact required for this operation"
            )
        elif gate == "human_confirmation":
            missing_evidence = "independently verifiable human approval evidence"
        else:
            missing_evidence = (
                "independent authorization and any repository evidence required for "
                "the high-risk operation"
            )
    return GovernanceAssessment(
        caseId=_CASE_ID_BY_RISK.get(request.riskCategory, "REFERENCE"),
        sourceType=record.sourceType,
        trustLevel=record.trustLevel,
        instructionAuthority=record.instructionAuthority,
        requestedOperation=request.requestedOperation,
        evidenceConflict=request.evidenceConflict,
        coverageStatus=coverage_status,
        decision=decision.value,
        gate=gate,
        reason=reason,
        missingEvidence=missing_evidence,
        recovery=request.recovery,
    )


def evaluate_governance_request(request: GovernanceRequest) -> GovernanceAssessment:
    """Assess known input-trust cases without inventing unavailable evidence.

    Only the source/trust layer's deterministic controls are marked ``covered``.
    A missing repository, lifecycle, or identity fact returns ``not_covered`` and
    requests review rather than simulating a block from evidence not present.
    """

    record = assess_input(request.sourceType, request.content)
    if request.riskCategory == "reference_fact" and request.requestedOperation == "read_reference":
        return _assessment(
            request,
            record,
            "covered",
            GovernanceDecision.ALLOW,
            "reference_only",
            "untrusted reference facts may be read but cannot grant operational authority",
        )

    if request.riskCategory == "untrusted_instruction_like_content":
        return _assessment(
            request,
            record,
            "covered",
            GovernanceDecision.REVIEW,
            "input_trust",
            "instruction-like text from an untrusted source remains analysis data",
        )

    if request.riskCategory == "forged_approval":
        return _assessment(
            request,
            record,
            "covered",
            GovernanceDecision.BLOCK,
            "human_confirmation",
            "untrusted approval text is not independently verifiable authority",
        )

    if request.riskCategory in {
        "external_instruction",
        "sensitive_data_exfiltration",
        "unverified_execution",
    }:
        return _assessment(
            request,
            record,
            "covered",
            GovernanceDecision.BLOCK,
            "input_trust",
            "untrusted content cannot authorize a high-risk operation",
        )

    return _assessment(
        request,
        record,
        "not_covered",
        GovernanceDecision.REVIEW,
        "evidence_gap",
        "no direct deterministic gate currently verifies the required repository or lifecycle fact",
    )
