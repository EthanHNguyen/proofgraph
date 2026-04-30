from pathlib import Path
from proofgraph.export.json_export import read_graph_json
from proofgraph.map_profile import map_profile


def test_map_profile_writes_expected_artifacts(tmp_path):
    graph, warnings, errors = map_profile('starter', 'examples/sample-repo', None, str(tmp_path), provider_name='offline')
    assert (tmp_path / 'control-map.json').exists()
    assert (tmp_path / 'control-map.md').exists()
    assert (tmp_path / 'poam.csv').exists()
    assert (tmp_path / 'evidence-index.csv').exists()
    assert (tmp_path / 'reviewer-questions.md').exists()
    assert (tmp_path / 'controls' / 'AU-6.md').exists()
    saved = read_graph_json(tmp_path / 'control-map.json')
    assert len(saved.controls) == 13
    assert all(claim.evidence_refs for claim in saved.claims)
