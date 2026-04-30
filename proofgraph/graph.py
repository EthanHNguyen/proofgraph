from __future__ import annotations

from collections import defaultdict

from proofgraph.schemas import AgentControlResult, Claim, Control, ControlEvidenceGraph, ControlStatus, EvidenceChunk, EvidenceSource, Gap, GraphEdge, GraphSummary, ReviewerQuestion


def new_graph(profile_id: str, controls: list[Control], sources: list[EvidenceSource], chunks: list[EvidenceChunk]) -> ControlEvidenceGraph:
    return ControlEvidenceGraph(profile_id=profile_id, controls=controls, sources=sources, chunks=chunks, control_status={c.id: ControlStatus.unknown for c in controls})


def import_control_result(graph: ControlEvidenceGraph, result: AgentControlResult) -> None:
    control_id = result.control_id
    graph.control_status[control_id] = result.status
    for idx, agent_claim in enumerate(result.claims, start=1):
        compact = control_id.replace('-', '')
        claim = Claim(
            id=f"CLAIM-{compact}-{idx:03d}",
            control_id=control_id,
            statement=agent_claim.statement,
            confidence=agent_claim.confidence,
            evidence_refs=agent_claim.evidence_refs,
        )
        graph.claims.append(claim)
        for ref in claim.evidence_refs:
            graph.edges.append(GraphEdge(from_=ref, to=claim.id, type='supports'))
        graph.edges.append(GraphEdge(from_=claim.id, to=control_id, type='supports' if result.status == ControlStatus.supported else 'partially_supports'))
    for idx, agent_gap in enumerate(result.gaps, start=1):
        compact = control_id.replace('-', '')
        gap = Gap(id=f"GAP-{compact}-{idx:03d}", control_id=control_id, statement=agent_gap.statement, reason=agent_gap.reason, recommended_action=agent_gap.recommended_action)
        graph.gaps.append(gap)
        graph.edges.append(GraphEdge(from_=gap.id, to=control_id, type='missing_for'))
    for idx, question in enumerate(result.reviewer_questions, start=1):
        compact = control_id.replace('-', '')
        rq = ReviewerQuestion(id=f"RQ-{compact}-{idx:03d}", control_id=control_id, question=question)
        graph.reviewer_questions.append(rq)
        graph.edges.append(GraphEdge(from_=rq.id, to=control_id, type='raises_question'))
    refresh_summary(graph)


def refresh_summary(graph: ControlEvidenceGraph) -> None:
    statuses = graph.control_status
    cited = {ref for claim in graph.claims for ref in claim.evidence_refs}
    graph.summary = GraphSummary(
        control_count=len(graph.controls),
        supported_controls=sum(1 for s in statuses.values() if s == ControlStatus.supported),
        partial_controls=sum(1 for s in statuses.values() if s == ControlStatus.partial),
        gap_controls=sum(1 for s in statuses.values() if s == ControlStatus.gap),
        unknown_controls=sum(1 for s in statuses.values() if s == ControlStatus.unknown),
        claim_count=len(graph.claims),
        gap_count=len(graph.gaps),
        evidence_count=len(cited),
    )


def claims_by_control(graph: ControlEvidenceGraph) -> dict[str, list[Claim]]:
    out: dict[str, list[Claim]] = defaultdict(list)
    for claim in graph.claims:
        out[claim.control_id].append(claim)
    return dict(out)


def gaps_by_control(graph: ControlEvidenceGraph) -> dict[str, list[Gap]]:
    out: dict[str, list[Gap]] = defaultdict(list)
    for gap in graph.gaps:
        out[gap.control_id].append(gap)
    return dict(out)


def questions_by_control(graph: ControlEvidenceGraph) -> dict[str, list[ReviewerQuestion]]:
    out: dict[str, list[ReviewerQuestion]] = defaultdict(list)
    for question in graph.reviewer_questions:
        out[question.control_id].append(question)
    return dict(out)


def chunk_lookup(graph: ControlEvidenceGraph) -> dict[str, EvidenceChunk]:
    return {chunk.id: chunk for chunk in graph.chunks}
