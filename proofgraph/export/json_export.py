from __future__ import annotations

import json
from pathlib import Path

from proofgraph.schemas import ControlEvidenceGraph


def write_graph_json(graph: ControlEvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.model_dump(by_alias=True, mode='json'), indent=2), encoding='utf-8')


def read_graph_json(path: Path) -> ControlEvidenceGraph:
    return ControlEvidenceGraph.model_validate_json(path.read_text(encoding='utf-8'))
