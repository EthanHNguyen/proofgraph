from proofgraph.map_profile import map_profile
from proofgraph.validate import contains_banned_language


def test_eval_fixtures_cover_semantic_failure_modes(tmp_path):
    graph, _, _ = map_profile('starter', 'examples/sample-repo', None, str(tmp_path), provider_name='offline')
    claims = ' '.join(claim.statement for claim in graph.claims)
    gaps = ' '.join(gap.statement for gap in graph.gaps)
    assert 'audit' in claims.lower()
    assert 'authentication' in claims.lower() or 'principal' in claims.lower()
    # Negative crypto doc must not create banned/compliance language.
    all_artifact_text = claims + ' ' + gaps
    assert not contains_banned_language(all_artifact_text)
    # Selected profile coverage.
    assert {control.id for control in graph.controls} == set(graph.control_status.keys())
