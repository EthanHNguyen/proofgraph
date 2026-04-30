from __future__ import annotations

from pathlib import Path

from proofgraph.graph import chunk_lookup, claims_by_control, gaps_by_control, questions_by_control
from proofgraph.schemas import ControlEvidenceGraph


def render_control_markdown(graph: ControlEvidenceGraph, control_id: str) -> str:
    controls = {control.id: control for control in graph.controls}
    control = controls[control_id]
    claims = claims_by_control(graph).get(control_id, [])
    gaps = gaps_by_control(graph).get(control_id, [])
    questions = questions_by_control(graph).get(control_id, [])
    chunks = chunk_lookup(graph)
    status = graph.control_status.get(control_id, 'unknown')
    status_text = status.value if hasattr(status, 'value') else str(status)
    lines = [f"# {control.id} {control.title}", "", f"Status: {status_text}", "", "## Source-backed implementation language", ""]
    if claims:
        lines.append("Available evidence supports the following implementation statements:")
        lines.append("")
        for claim in claims:
            lines.append(f"- {claim.statement}")
            for ref in claim.evidence_refs:
                chunk = chunks[ref]
                lines.append(f"  - Evidence: `{chunk.path}:{chunk.line_start}-{chunk.line_end}` hash `{chunk.sha256[:12]}`")
    else:
        lines.append("No source-backed implementation statements were validated for this control.")
    lines.extend(["", "## Evidence gaps / requires human input", ""])
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap.statement}")
            if gap.recommended_action:
                lines.append(f"  - Recommended action: {gap.recommended_action}")
    else:
        lines.append("- None identified by this run.")
    lines.extend(["", "## Reviewer questions", ""])
    if questions:
        for question in questions:
            lines.append(f"- {question.question}")
    else:
        lines.append("- None generated.")
    return "\n".join(lines).strip() + "\n"


def render_control_map_markdown(graph: ControlEvidenceGraph) -> str:
    cb = claims_by_control(graph)
    gb = gaps_by_control(graph)
    lines = ["# Control Artifact Map", "", f"Profile: `{graph.profile_id}`", "", "## Summary", "", "| Control | Status | Claims | Gaps | Evidence |", "|---|---:|---:|---:|---:|"]
    for control in graph.controls:
        claims = cb.get(control.id, [])
        gaps = gb.get(control.id, [])
        evidence_count = len({ref for claim in claims for ref in claim.evidence_refs})
        status = graph.control_status.get(control.id, 'unknown')
        status_text = status.value if hasattr(status, 'value') else str(status)
        lines.append(f"| {control.id} {control.title} | {status_text} | {len(claims)} | {len(gaps)} | {evidence_count} |")
    return "\n".join(lines).strip() + "\n"


def render_reviewer_questions_markdown(graph: ControlEvidenceGraph) -> str:
    qb = questions_by_control(graph)
    lines = ["# Reviewer Questions", ""]
    for control in graph.controls:
        questions = qb.get(control.id, [])
        if not questions:
            continue
        lines.extend([f"## {control.id} {control.title}", ""])
        for question in questions:
            lines.append(f"- {question.question}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_markdown_artifacts(graph: ControlEvidenceGraph, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'control-map.md').write_text(render_control_map_markdown(graph), encoding='utf-8')
    (output_dir / 'reviewer-questions.md').write_text(render_reviewer_questions_markdown(graph), encoding='utf-8')
    controls_dir = output_dir / 'controls'
    controls_dir.mkdir(exist_ok=True)
    for control in graph.controls:
        (controls_dir / f'{control.id}.md').write_text(render_control_markdown(graph, control.id), encoding='utf-8')
