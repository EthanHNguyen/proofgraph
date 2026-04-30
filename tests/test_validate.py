import pytest
from proofgraph.schemas import AgentClaim, AgentControlResult, ControlStatus
from proofgraph.validate import ValidationError, validate_agent_result
from proofgraph.inventory import inventory_paths
from proofgraph.profiles import load_profile


def test_validator_rejects_unknown_evidence_refs():
    control = next(c for c in load_profile('starter').controls if c.id == 'AU-6')
    _, chunks, _ = inventory_paths(['examples/sample-repo'])
    result = AgentControlResult(control_id='AU-6', status=ControlStatus.supported, claims=[AgentClaim(statement='Evidence supports audit logging.', evidence_refs=['EV-DOES-NOT-EXIST'], confidence='high')])
    with pytest.raises(ValidationError):
        validate_agent_result(result, control, chunks)


def test_validator_rejects_banned_language():
    control = next(c for c in load_profile('starter').controls if c.id == 'AU-6')
    _, chunks, _ = inventory_paths(['examples/sample-repo'])
    result = AgentControlResult(control_id='AU-6', status=ControlStatus.supported, claims=[AgentClaim(statement='The system is compliant with AU-6.', evidence_refs=[chunks[0].id], confidence='high')])
    with pytest.raises(ValidationError):
        validate_agent_result(result, control, chunks)
