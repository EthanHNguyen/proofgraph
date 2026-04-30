from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from proofgraph.export.json_export import read_graph_json
from proofgraph.explain import explain_control
from proofgraph.inventory import inventory_paths, write_evidence_index_csv
from proofgraph.map_profile import map_one_control, map_profile
from proofgraph.profiles import list_profiles, load_profile

app = typer.Typer(help='ProofGraph: map what your system proves.')
profiles_app = typer.Typer(help='Profile commands')
app.add_typer(profiles_app, name='profiles')


@profiles_app.command('list')
def profiles_list():
    for profile in list_profiles():
        typer.echo(f"{profile.id}\t{profile.name}\t{len(profile.controls)} controls")


@profiles_app.command('show')
def profiles_show(profile: str = 'starter'):
    loaded = load_profile(profile)
    typer.echo(f"{loaded.id}: {loaded.name}")
    for control in loaded.controls:
        typer.echo(f"  {control.id}\t{control.title}")


@app.command()
def inventory(path: str, out: str = './out'):
    sources, chunks, warnings = inventory_paths([path])
    output = Path(out)
    write_evidence_index_csv(chunks, output / 'evidence-index.csv')
    typer.echo(f"Files scanned: {len(sources)}")
    typer.echo(f"Evidence chunks: {len(chunks)}")
    typer.echo(f"Wrote {output / 'evidence-index.csv'}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command('map-control')
def map_control(control_id: str, profile: str = 'starter', repo: Optional[str] = None, evidence: Optional[str] = None, out: str = './out', provider: Optional[str] = None, strict: bool = False):
    graph, warnings = map_one_control(control_id, profile, repo, evidence, out, provider, strict)
    typer.echo(f"Mapped {control_id.upper()}: {graph.summary.claim_count} claims, {graph.summary.gap_count} gaps")
    typer.echo(f"Wrote artifacts to {Path(out).resolve()}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command('map')
def map_cmd(profile: str = 'starter', repo: Optional[str] = None, evidence: Optional[str] = None, out: str = './out', provider: Optional[str] = None, strict: bool = False):
    if not repo and not evidence:
        raise typer.BadParameter('provide --repo and/or --evidence')
    graph, warnings, validation_errors = map_profile(profile, repo, evidence, out, provider, strict)
    typer.echo('ProofGraph')
    typer.echo(f"Profile: {graph.profile_id}")
    typer.echo(f"Controls: {graph.summary.control_count}")
    typer.echo(f"Claims: {graph.summary.claim_count}")
    typer.echo(f"Gaps: {graph.summary.gap_count}")
    typer.echo(f"Evidence entries: {graph.summary.evidence_count}")
    typer.echo(f"Wrote artifacts to {Path(out).resolve()}")
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)
    for error in validation_errors:
        typer.echo(f"validation warning: {error}", err=True)


@app.command('validate')
def validate_graph(path: str):
    graph = read_graph_json(Path(path))
    chunk_ids = {chunk.id for chunk in graph.chunks}
    control_ids = {control.id for control in graph.controls}
    for claim in graph.claims:
        if claim.control_id not in control_ids:
            raise typer.BadParameter(f"claim references non-selected control: {claim.control_id}")
        for ref in claim.evidence_refs:
            if ref not in chunk_ids:
                raise typer.BadParameter(f"claim {claim.id} references unknown evidence {ref}")
    typer.echo(f"OK: {len(graph.controls)} controls, {len(graph.claims)} claims, {len(graph.gaps)} gaps")


@app.command('explain')
def explain(control_id: str, from_: str = typer.Option(..., '--from')):
    graph = read_graph_json(Path(from_))
    typer.echo(explain_control(graph, control_id))
