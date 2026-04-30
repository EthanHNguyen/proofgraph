import pytest
from proofgraph.profiles import load_profile


def test_loads_starter_profile_with_all_controls():
    profile = load_profile('starter')
    assert profile.id == 'starter-security-profile'
    assert len(profile.controls) == 13
    assert {c.id for c in profile.controls} >= {'AC-2','AU-6','IA-2','SC-7','SI-4'}


def test_duplicate_controls_fail_validation():
    from proofgraph.schemas import Profile
    with pytest.raises(ValueError):
        Profile.model_validate({'id':'x','name':'x','controls':[{'id':'AU-6','title':'A','objective':'o'}, {'id':'AU-6','title':'B','objective':'o'}]})
