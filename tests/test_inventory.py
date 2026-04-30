from proofgraph.inventory import inventory_paths


def test_inventory_scans_sample_repo_with_line_chunks():
    sources, chunks, warnings = inventory_paths(['examples/sample-repo'])
    assert not warnings
    assert any(s.path == 'app/admin.py' for s in sources)
    assert any(c.path == 'app/admin.py' and c.line_start >= 1 for c in chunks)
    assert all(c.id.startswith('EV-') for c in chunks)
