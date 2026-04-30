from __future__ import annotations

import csv
from pathlib import Path

from proofgraph.chunking import chunk_source, make_source
from proofgraph.schemas import EvidenceChunk, EvidenceSource

ALLOWED_SUFFIXES = {'.py', '.js', '.ts', '.tsx', '.go', '.java', '.rb', '.json', '.yaml', '.yml', '.toml', '.ini', '.tf', '.md', '.txt', '.log', '.csv'}
SKIP_DIRS = {'.git', 'node_modules', 'dist', 'build', '.next', '__pycache__', '.venv', 'vendor'}
MAX_FILE_BYTES = 500_000


def should_scan(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in ALLOWED_SUFFIXES


def inventory_paths(paths: list[str | Path]) -> tuple[list[EvidenceSource], list[EvidenceChunk], list[str]]:
    sources: list[EvidenceSource] = []
    chunks: list[EvidenceChunk] = []
    warnings: list[str] = []
    files: list[tuple[Path, Path]] = []
    for input_path in paths:
        root = Path(input_path)
        if not root.exists():
            warnings.append(f"missing path: {root}")
            continue
        resolved_root = root.resolve()
        if root.is_file():
            if root.is_symlink():
                warnings.append(f"skipped symlinked file: {root}")
                continue
            files.append((root.parent, root))
        else:
            for path in sorted(root.rglob('*')):
                if path.is_symlink():
                    warnings.append(f"skipped symlink: {path}")
                    continue
                if not path.resolve().is_relative_to(resolved_root):
                    warnings.append(f"skipped path outside root: {path}")
                    continue
                if path.is_file() and should_scan(path.relative_to(root)):
                    files.append((root, path))
    chunk_index = 1
    for source_index, (root, path) in enumerate(files, start=1):
        relative = str(path.relative_to(root))
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                warnings.append(f"skipped oversized file: {relative}")
                continue
            content = path.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            warnings.append(f"skipped unreadable file {relative}: {exc}")
            continue
        source = make_source(source_index, relative, content)
        source_chunks = chunk_source(source, content, start_index=chunk_index)
        sources.append(source)
        chunks.extend(source_chunks)
        chunk_index += len(source_chunks)
    return sources, chunks, warnings


def write_evidence_index_csv(chunks: list[EvidenceChunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['evidence_id','path','line_start','line_end','sha256','kind','supports_claims','supports_controls','excerpt'])
        writer.writeheader()
        for chunk in chunks:
            writer.writerow({
                'evidence_id': chunk.id,
                'path': chunk.path,
                'line_start': chunk.line_start,
                'line_end': chunk.line_end,
                'sha256': chunk.sha256,
                'kind': chunk.kind.value,
                'supports_claims': '',
                'supports_controls': '',
                'excerpt': chunk.text[:240].replace('\n', ' '),
            })
