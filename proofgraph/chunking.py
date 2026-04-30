from __future__ import annotations

import hashlib
from pathlib import Path

from proofgraph.schemas import EvidenceChunk, EvidenceKind, EvidenceSource

CHUNK_LINES = 40
OVERLAP_LINES = 5


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def kind_for_path(path: str) -> EvidenceKind:
    lower = path.lower()
    suffix = Path(lower).suffix
    if suffix in {".py", ".js", ".ts", ".tsx", ".go", ".java", ".rb"}:
        return EvidenceKind.source
    if suffix in {".tf"} or any(part in lower for part in ["infra/", "terraform", "k8s", "kubernetes"]):
        return EvidenceKind.infrastructure
    if suffix in {".yaml", ".yml", ".json", ".toml", ".ini"}:
        return EvidenceKind.config
    if suffix == ".log":
        return EvidenceKind.log
    if suffix == ".csv":
        return EvidenceKind.data
    if suffix in {".md", ".txt"} and any(term in lower for term in ["runbook", "review", "procedure"]):
        return EvidenceKind.runbook
    if suffix in {".md", ".txt"}:
        return EvidenceKind.policy
    return EvidenceKind.unknown


def make_source(source_number: int, relative_path: str, content: str) -> EvidenceSource:
    return EvidenceSource(
        id=f"SRC-{source_number:04d}",
        path=relative_path,
        kind=kind_for_path(relative_path),
        sha256=sha256_text(content),
        size_bytes=len(content.encode("utf-8", errors="replace")),
    )


def chunk_source(source: EvidenceSource, content: str, start_index: int = 1, chunk_lines: int = CHUNK_LINES) -> list[EvidenceChunk]:
    lines = content.splitlines()
    if not lines:
        lines = [""]
    chunks: list[EvidenceChunk] = []
    step = max(1, chunk_lines - OVERLAP_LINES)
    chunk_number = start_index
    for idx in range(0, len(lines), step):
        selected = lines[idx: idx + chunk_lines]
        if not selected:
            continue
        text = "\n".join(selected)
        chunks.append(EvidenceChunk(
            id=f"EV-{chunk_number:04d}",
            source_id=source.id,
            path=source.path,
            line_start=idx + 1,
            line_end=idx + len(selected),
            sha256=sha256_text(text),
            text=text,
            kind=source.kind,
        ))
        chunk_number += 1
        if idx + chunk_lines >= len(lines):
            break
    return chunks
