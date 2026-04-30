from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional

import typer

from proofgraph.export.json_export import read_graph_json
from proofgraph.explain import explain_control
from proofgraph.inventory import inventory_paths, write_evidence_index_csv
from proofgraph.map_profile import map_one_control, map_profile
from proofgraph.profiles import list_profiles, load_profile
from proofgraph.validate import validate_graph_model

app = typer.Typer(help='ProofGraph: map what your system proves.')
profiles_app = typer.Typer(help='Profile commands')
app.add_typer(profiles_app, name='profiles')

DEFAULT_OUT = './proofgraph-out'
SAMPLE_REPO_PACKAGE = 'proofgraph.bundled_sample'
SAMPLE_REPO_RESOURCE = 'sample-repo'


def _require_existing_path(path: str | None, label: str) -> None:
    if path and not Path(path).exists():
        raise typer.BadParameter(f'{label} path does not exist: {path}')


def _print_run_summary(graph, out: str, validation_errors: list[str] | None = None) -> None:
    output_dir = Path(out).resolve()
    typer.echo('ProofGraph')
    typer.echo(f"Profile: {graph.profile_id}")
    typer.echo(f"Controls: {graph.summary.control_count}")
    typer.echo(f"Claims: {graph.summary.claim_count}")
    typer.echo(f"Gaps: {graph.summary.gap_count}")
    typer.echo(f"Evidence entries: {graph.summary.evidence_count}")
    typer.echo(f"Wrote artifacts to {output_dir}")
    if validation_errors:
        for error in validation_errors:
            typer.echo(f"validation warning: {error}", err=True)
    typer.echo('')
    typer.echo('Next:')
    typer.echo(f"  proofgraph explain AU-6 --from {output_dir / 'control-map.json'}")
    typer.echo(f"  proofgraph validate {output_dir / 'control-map.json'}")


def _map_and_validate(
    target: str,
    profile: str,
    out: str,
    provider: Optional[str],
    evidence: Optional[str],
    strict: bool,
):
    _require_existing_path(target, 'target')
    _require_existing_path(evidence, 'evidence')
    try:
        graph, warnings, validation_errors = map_profile(profile, target, evidence, out, provider, strict)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    validate_graph_model(graph)
    _print_run_summary(graph, out, validation_errors)
    typer.echo(f"Validated graph: {Path(out).resolve() / 'control-map.json'}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)
    return graph


@profiles_app.command('list')
def profiles_list():
    """List bundled and local control profiles."""
    for profile in list_profiles():
        typer.echo(f"{profile.id}\t{profile.name}\t{len(profile.controls)} controls")


@profiles_app.command('show')
def profiles_show(profile: str = typer.Argument('starter')):
    """Show controls in a profile."""
    loaded = load_profile(profile)
    typer.echo(f"{loaded.id}: {loaded.name}")
    for control in loaded.controls:
        typer.echo(f"  {control.id}\t{control.title}")


@app.command()
def run(
    target: str = typer.Argument(..., help='Repo or evidence folder to scan.'),
    profile: str = typer.Option('starter', '--profile', '-p', help='Control profile to use.'),
    out: str = typer.Option(DEFAULT_OUT, '--out', '-o', help='Output directory.'),
    provider: Optional[str] = typer.Option(None, '--provider', help='Agent provider: offline or openai. Defaults to PROOFGRAPH_PROVIDER/offline.'),
    evidence: Optional[str] = typer.Option(None, '--evidence', '-e', help='Optional extra evidence folder.'),
    strict: bool = typer.Option(False, '--strict', help='Fail on the first invalid agent result.'),
):
    """One-command path: map a repo, validate the graph, and write artifacts."""
    _map_and_validate(target, profile, out, provider, evidence, strict)


@app.command()
def demo(out: str = typer.Option(DEFAULT_OUT, '--out', '-o', help='Output directory.')):
    """Run ProofGraph against the bundled synthetic sample."""
    sample = files(SAMPLE_REPO_PACKAGE) / SAMPLE_REPO_RESOURCE
    with as_file(sample) as sample_path:
        _map_and_validate(str(sample_path), 'starter', out, 'offline', None, False)
    typer.echo('ProofGraph demo complete')


@app.command()
def inventory(path: str, out: str = './out'):
    """Write a CSV evidence index for a path."""
    sources, chunks, warnings = inventory_paths([path])
    output = Path(out)
    write_evidence_index_csv(chunks, output / 'evidence-index.csv')
    typer.echo(f"Files scanned: {len(sources)}")
    typer.echo(f"Evidence chunks: {len(chunks)}")
    typer.echo(f"Wrote {output / 'evidence-index.csv'}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command('map-control')
def map_control(
    control_id: str,
    target: Optional[str] = typer.Argument(None, help='Repo or evidence folder to scan.'),
    profile: str = typer.Option('starter', '--profile', '-p'),
    repo: Optional[str] = typer.Option(None, '--repo', help='Repo path. Kept for backwards compatibility.'),
    evidence: Optional[str] = typer.Option(None, '--evidence', '-e'),
    out: str = typer.Option(DEFAULT_OUT, '--out', '-o'),
    provider: Optional[str] = typer.Option(None, '--provider'),
    strict: bool = typer.Option(False, '--strict'),
):
    """Map one control for focused review."""
    repo_path = repo or target
    if not repo_path and not evidence:
        raise typer.BadParameter('provide a target path, --repo, or --evidence')
    _require_existing_path(repo_path, 'repo')
    _require_existing_path(evidence, 'evidence')
    try:
        graph, warnings = map_one_control(control_id, profile, repo_path, evidence, out, provider, strict)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Mapped {control_id.upper()}: {graph.summary.claim_count} claims, {graph.summary.gap_count} gaps")
    typer.echo(f"Wrote artifacts to {Path(out).resolve()}")
    typer.echo(f"Next: proofgraph explain {control_id.upper()} --from {Path(out).resolve() / 'control-map.json'}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command('map')
def map_cmd(
    target: Optional[str] = typer.Argument(None, help='Repo or evidence folder to scan.'),
    profile: str = typer.Option('starter', '--profile', '-p'),
    repo: Optional[str] = typer.Option(None, '--repo', help='Repo path. Kept for backwards compatibility.'),
    evidence: Optional[str] = typer.Option(None, '--evidence', '-e'),
    out: str = typer.Option(DEFAULT_OUT, '--out', '-o'),
    provider: Optional[str] = typer.Option(None, '--provider'),
    strict: bool = typer.Option(False, '--strict'),
):
    """Map a profile to cited artifacts. Prefer `proofgraph run PATH` for the full validated flow."""
    repo_path = repo or target
    if not repo_path and not evidence:
        raise typer.BadParameter('provide a target path, --repo, or --evidence')
    _require_existing_path(repo_path, 'repo')
    _require_existing_path(evidence, 'evidence')
    try:
        graph, warnings, validation_errors = map_profile(profile, repo_path, evidence, out, provider, strict)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _print_run_summary(graph, out, validation_errors)
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command('validate')
def validate_graph(path: str):
    """Validate a generated control-map.json graph."""
    graph = read_graph_json(Path(path))
    try:
        validate_graph_model(graph)
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"OK: {len(graph.controls)} controls, {len(graph.claims)} claims, {len(graph.gaps)} gaps")


@app.command('explain')
def explain(control_id: str, from_: str = typer.Option(..., '--from')):
    """Explain one control using cited graph evidence."""
    graph = read_graph_json(Path(from_))
    typer.echo(explain_control(graph, control_id))
