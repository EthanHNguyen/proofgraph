from __future__ import annotations

import re
from collections import Counter

from proofgraph.schemas import Control, EvidenceChunk

PATH_WEIGHTS = {
    'auth': 4, 'identity': 4, 'admin': 4, 'security': 4, 'logging': 4,
    'audit': 4, 'infra': 3, 'terraform': 3, 'network': 3, 'docs': 2,
    'runbook': 3, 'monitor': 3, 'alert': 3,
}
FILE_KIND_WEIGHTS = {
    'source': 2, 'config': 2, 'infrastructure': 3, 'policy': 1, 'runbook': 2, 'log': 1, 'data': 1, 'unknown': 0,
}


def terms(text: str) -> list[str]:
    return [term for term in re.split(r'[^a-z0-9]+', text.lower()) if len(term) >= 3]


def score_chunk(control: Control, chunk: EvidenceChunk) -> int:
    haystack = f"{chunk.path}\n{chunk.text}".lower()
    control_terms = Counter(terms(' '.join([control.id, control.title, control.objective, *control.evidence_hints])))
    score = 0
    for term, count in control_terms.items():
        if term in haystack:
            score += min(3, count)
    lower_path = chunk.path.lower()
    for path_term, weight in PATH_WEIGHTS.items():
        if path_term in lower_path:
            score += weight
    score += FILE_KIND_WEIGHTS.get(chunk.kind.value, 0)
    if control.id.split('-')[0].lower() in haystack:
        score += 2
    return score


def retrieve_candidates(control: Control, chunks: list[EvidenceChunk], limit: int = 25) -> list[EvidenceChunk]:
    ranked = sorted(chunks, key=lambda chunk: (score_chunk(control, chunk), -chunk.line_start), reverse=True)
    return [chunk for chunk in ranked if score_chunk(control, chunk) > 0][:limit]
