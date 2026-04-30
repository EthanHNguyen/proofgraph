from __future__ import annotations

import re

from proofgraph.schemas import AgentControlResult, Control, ControlEvidenceGraph, EvidenceChunk

BANNED_PATTERNS = [
    r'\bcompliant\b', r'\bcertified\b', r'\bauthorized\b', r'ATO-ready', r'audit-ready',
    r'meets\s+FedRAMP', r'satisfies\s+NIST', r'fully\s+implemented',
]


class ValidationError(Exception):
    pass


def contains_banned_language(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in BANNED_PATTERNS)


def validate_graph_model(graph: ControlEvidenceGraph) -> None:
    control_ids = {control.id for control in graph.controls}
    chunk_ids = {chunk.id for chunk in graph.chunks}
    claim_ids = {claim.id for claim in graph.claims}
    gap_ids = {gap.id for gap in graph.gaps}
    question_ids = {question.id for question in graph.reviewer_questions}
    all_node_ids = control_ids | chunk_ids | claim_ids | gap_ids | question_ids

    for collection_name, ids in {
        'controls': [control.id for control in graph.controls],
        'chunks': [chunk.id for chunk in graph.chunks],
        'claims': [claim.id for claim in graph.claims],
        'gaps': [gap.id for gap in graph.gaps],
        'reviewer_questions': [question.id for question in graph.reviewer_questions],
    }.items():
        if len(ids) != len(set(ids)):
            raise ValidationError(f'duplicate ids in {collection_name}')

    for claim in graph.claims:
        if claim.control_id not in control_ids:
            raise ValidationError(f'claim references non-selected control: {claim.control_id}')
        if contains_banned_language(claim.statement):
            raise ValidationError(f'claim contains banned language: {claim.id}')
        if not claim.evidence_refs:
            raise ValidationError(f'claim lacks evidence refs: {claim.id}')
        for ref in claim.evidence_refs:
            if ref not in chunk_ids:
                raise ValidationError(f'claim {claim.id} references unknown evidence {ref}')

    for gap in graph.gaps:
        if gap.control_id not in control_ids:
            raise ValidationError(f'gap references non-selected control: {gap.control_id}')
        if contains_banned_language(gap.statement) or contains_banned_language(gap.reason):
            raise ValidationError(f'gap contains banned language: {gap.id}')

    for question in graph.reviewer_questions:
        if question.control_id not in control_ids:
            raise ValidationError(f'question references non-selected control: {question.control_id}')
        if contains_banned_language(question.question):
            raise ValidationError(f'question contains banned language: {question.id}')

    for edge in graph.edges:
        if edge.from_ not in all_node_ids:
            raise ValidationError(f'edge references unknown from node: {edge.from_}')
        if edge.to not in all_node_ids:
            raise ValidationError(f'edge references unknown to node: {edge.to}')

    if set(graph.control_status.keys()) != control_ids:
        raise ValidationError('control_status keys must exactly match graph controls')
    if graph.summary.control_count != len(graph.controls):
        raise ValidationError('summary control_count mismatch')
    if graph.summary.claim_count != len(graph.claims):
        raise ValidationError('summary claim_count mismatch')
    if graph.summary.gap_count != len(graph.gaps):
        raise ValidationError('summary gap_count mismatch')


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
