from __future__ import annotations

from pathlib import Path

from proofgraph.agent_mapper import get_provider
from proofgraph.export.csv_export import write_evidence_index_csv, write_poam_csv
from proofgraph.export.json_export import write_graph_json
from proofgraph.export.markdown_export import write_markdown_artifacts
from proofgraph.graph import import_control_result, new_graph, refresh_summary
from proofgraph.inventory import inventory_paths
from proofgraph.profiles import load_profile
from proofgraph.retrieval import retrieve_candidates
from proofgraph.schemas import AgentControlResult, AgentGap, ControlStatus
from proofgraph.validate import ValidationError, validate_agent_result


def map_profile(profile_path: str, repo: str | None, evidence: str | None, out: str, provider_name: str | None = None, strict: bool = False):
    profile = load_profile(profile_path)
    paths = [p for p in [repo, evidence] if p]
    sources, chunks, warnings = inventory_paths(paths)
    graph = new_graph(profile.id, profile.controls, sources, chunks)
    provider = get_provider(provider_name)
    validation_errors: list[str] = []
    for control in profile.controls:
        candidates = retrieve_candidates(control, chunks)
        try:
            result = provider.map_control(control, candidates)
            result = validate_agent_result(result, control, chunks)
        except Exception as exc:
            validation_errors.append(f"{control.id}: {exc}")
            if strict:
                raise
            result = AgentControlResult(
                control_id=control.id,
                status=ControlStatus.unknown,
                claims=[],
                gaps=[AgentGap(statement='Agent output failed validation; human review required.', reason=str(exc), recommended_action='Review evidence manually or rerun with a configured provider.')],
                reviewer_questions=[f'What evidence should a reviewer inspect for {control.id}?'],
            )
        import_control_result(graph, result)
    refresh_summary(graph)
    output_dir = Path(out)
    write_graph_json(graph, output_dir / 'control-map.json')
    write_markdown_artifacts(graph, output_dir)
    write_poam_csv(graph, output_dir / 'poam.csv')
    write_evidence_index_csv(graph, output_dir / 'evidence-index.csv')
    return graph, warnings, validation_errors


def map_one_control(control_id: str, profile_path: str, repo: str | None, evidence: str | None, out: str, provider_name: str | None = None, strict: bool = False):
    profile = load_profile(profile_path)
    wanted = control_id.upper()
    controls = [control for control in profile.controls if control.id == wanted]
    if not controls:
        raise ValueError(f'control {wanted} not in profile {profile.id}')
    paths = [p for p in [repo, evidence] if p]
    sources, chunks, warnings = inventory_paths(paths)
    graph = new_graph(profile.id, controls, sources, chunks)
    provider = get_provider(provider_name)
    control = controls[0]
    candidates = retrieve_candidates(control, chunks)
    result = provider.map_control(control, candidates)
    result = validate_agent_result(result, control, chunks)
    import_control_result(graph, result)
    refresh_summary(graph)
    output_dir = Path(out)
    write_graph_json(graph, output_dir / 'control-map.json')
    write_markdown_artifacts(graph, output_dir)
    write_poam_csv(graph, output_dir / 'poam.csv')
    write_evidence_index_csv(graph, output_dir / 'evidence-index.csv')
    return graph, warnings
