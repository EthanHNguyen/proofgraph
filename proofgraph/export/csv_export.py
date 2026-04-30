from __future__ import annotations

import csv
from pathlib import Path

from proofgraph.graph import chunk_lookup, claims_by_control
from proofgraph.schemas import ControlEvidenceGraph


def write_poam_csv(graph: ControlEvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        fields = ['id','control_id','weakness','evidence_status','risk','recommended_action','evidence_needed','status','owner','target_date']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for gap in graph.gaps:
            writer.writerow({
                'id': gap.id,
                'control_id': gap.control_id,
                'weakness': gap.statement,
                'evidence_status': 'gap',
                'risk': f'Reviewer may reject {gap.control_id} evidence because {gap.statement[0].lower() + gap.statement[1:]}',
                'recommended_action': gap.recommended_action,
                'evidence_needed': 'Source/config/policy/runbook evidence with citation.',
                'status': 'Open',
                'owner': 'Human input required',
                'target_date': 'Human input required',
            })


def write_evidence_index_csv(graph: ControlEvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    claim_controls: dict[str, list[str]] = {}
    claim_ids: dict[str, list[str]] = {}
    for claim in graph.claims:
        for ref in claim.evidence_refs:
            claim_controls.setdefault(ref, []).append(claim.control_id)
            claim_ids.setdefault(ref, []).append(claim.id)
    with path.open('w', encoding='utf-8', newline='') as f:
        fields = ['evidence_id','path','line_start','line_end','sha256','kind','supports_claims','supports_controls','excerpt']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for chunk in graph.chunks:
            if chunk.id not in claim_ids:
                continue
            writer.writerow({
                'evidence_id': chunk.id,
                'path': chunk.path,
                'line_start': chunk.line_start,
                'line_end': chunk.line_end,
                'sha256': chunk.sha256,
                'kind': chunk.kind.value,
                'supports_claims': ';'.join(claim_ids.get(chunk.id, [])),
                'supports_controls': ';'.join(sorted(set(claim_controls.get(chunk.id, [])))),
                'excerpt': chunk.text[:240].replace('\n', ' '),
            })
