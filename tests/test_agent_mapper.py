import pytest
from proofgraph.agent_mapper import OfflineSemanticAgentProvider, parse_agent_json
from proofgraph.inventory import inventory_paths
from proofgraph.profiles import load_profile
from proofgraph.retrieval import retrieve_candidates


def test_parse_agent_json_rejects_invalid_json():
    with pytest.raises(Exception):
        parse_agent_json('not json')


def test_offline_agent_maps_au6_semantic_claims_and_gaps():
    profile = load_profile('starter')
    control = next(c for c in profile.controls if c.id == 'AU-6')
    _, chunks, _ = inventory_paths(['examples/sample-repo'])
    result = OfflineSemanticAgentProvider().map_control(control, retrieve_candidates(control, chunks))
    assert result.control_id == 'AU-6'
    assert result.claims
    assert all(claim.evidence_refs for claim in result.claims)
