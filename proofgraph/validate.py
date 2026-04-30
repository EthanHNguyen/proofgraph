from __future__ import annotations

import re

from proofgraph.schemas import AgentControlResult, Control, EvidenceChunk

BANNED_PATTERNS = [
    r'\bcompliant\b', r'\bcertified\b', r'\bauthorized\b', r'ATO-ready', r'audit-ready',
    r'meets\s+FedRAMP', r'satisfies\s+NIST', r'fully\s+implemented',
]


class ValidationError(Exception):
    pass


def contains_banned_language(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in BANNED_PATTERNS)


def validate_agent_result(result: AgentControlResult, control: Control, chunks: list[EvidenceChunk]) -> AgentControlResult:
    if result.control_id != control.id:
        raise ValidationError(f"agent returned {result.control_id}, expected {control.id}")
    chunk_ids = {chunk.id for chunk in chunks}
    for claim in result.claims:
        if not claim.evidence_refs:
            raise ValidationError(f"claim lacks evidence refs: {claim.statement}")
        if contains_banned_language(claim.statement):
            raise ValidationError(f"claim contains banned language: {claim.statement}")
        unknown = [ref for ref in claim.evidence_refs if ref not in chunk_ids]
        if unknown:
            raise ValidationError(f"claim cites unknown evidence refs: {unknown}")
    for gap in result.gaps:
        if contains_banned_language(gap.statement) or contains_banned_language(gap.reason):
            raise ValidationError(f"gap contains banned language: {gap.statement}")
    for question in result.reviewer_questions:
        if contains_banned_language(question):
            raise ValidationError(f"question contains banned language: {question}")
    if result.status.value == 'supported' and result.gaps:
        result.status = type(result.status).partial
    return result
