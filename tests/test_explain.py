from proofgraph.explain import explain_control
from proofgraph.map_profile import map_profile


def test_explain_control_outputs_supported_and_missing_sections(tmp_path):
    graph, _, _ = map_profile('starter', 'examples/sample-repo', None, str(tmp_path), provider_name='offline')
    text = explain_control(graph, 'AU-6')
    assert 'AU-6' in text
    assert 'Supported claims' in text
    assert 'Missing evidence' in text
