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
