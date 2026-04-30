from proofgraph.agent_mapper import OfflineSemanticAgentProvider
from proofgraph.graph import import_control_result, new_graph
from proofgraph.inventory import inventory_paths
from proofgraph.profiles import load_profile
from proofgraph.retrieval import retrieve_candidates


def test_graph_import_creates_claim_and_control_edges():
    profile = load_profile('starter')
    control = next(c for c in profile.controls if c.id == 'AU-6')
    sources, chunks, _ = inventory_paths(['examples/sample-repo'])
    graph = new_graph(profile.id, [control], sources, chunks)
    result = OfflineSemanticAgentProvider().map_control(control, retrieve_candidates(control, chunks))
    import_control_result(graph, result)
    assert graph.claims
    assert any(edge.type == 'supports' for edge in graph.edges)
