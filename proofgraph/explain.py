from __future__ import annotations

from proofgraph.graph import chunk_lookup, claims_by_control, gaps_by_control, questions_by_control
from proofgraph.schemas import ControlEvidenceGraph


def explain_control(graph: ControlEvidenceGraph, control_id: str) -> str:
    control_id = control_id.upper()
    controls = {control.id: control for control in graph.controls}
    if control_id not in controls:
        raise KeyError(f'control not found: {control_id}')
    control = controls[control_id]
    chunks = chunk_lookup(graph)
    status = graph.control_status.get(control_id, 'unknown')
    status_text = status.value if hasattr(status, 'value') else str(status)
    lines = [f"{control.id} {control.title}", f"Status: {status_text}", "", "Supported claims:"]
    claims = claims_by_control(graph).get(control_id, [])
    if claims:
        for claim in claims:
            lines.append(f"  ✓ {claim.statement}")
            for ref in claim.evidence_refs:
                chunk = chunks[ref]
                lines.append(f"    - {chunk.path}:{chunk.line_start}-{chunk.line_end} hash {chunk.sha256[:12]}")
    else:
        lines.append("  - None")
    lines.extend(["", "Missing evidence:"])
    gaps = gaps_by_control(graph).get(control_id, [])
    if gaps:
        for gap in gaps:
            lines.append(f"  ✕ {gap.statement}")
    else:
        lines.append("  - None")
    lines.extend(["", "Reviewer questions:"])
    questions = questions_by_control(graph).get(control_id, [])
    if questions:
        for question in questions:
            lines.append(f"  - {question.question}")
    else:
        lines.append("  - None")
    return "\n".join(lines)
