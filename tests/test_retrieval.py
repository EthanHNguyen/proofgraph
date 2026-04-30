from proofgraph.inventory import inventory_paths
from proofgraph.profiles import load_profile
from proofgraph.retrieval import retrieve_candidates


def _control(cid):
    return next(c for c in load_profile('starter').controls if c.id == cid)


def test_au6_retrieves_audit_chunks():
    _, chunks, _ = inventory_paths(['examples/sample-repo'])
    candidates = retrieve_candidates(_control('AU-6'), chunks)
    assert any('admin.py' in c.path or 'audit' in c.path.lower() for c in candidates[:5])


def test_sc7_retrieves_network_chunks():
    _, chunks, _ = inventory_paths(['examples/sample-repo'])
    candidates = retrieve_candidates(_control('SC-7'), chunks)
    assert any('network' in c.path.lower() for c in candidates[:5])
