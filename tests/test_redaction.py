from proofgraph.redaction import redact_text


def test_redacts_common_secret_patterns():
    text = "api_key='sk-abcdefghijklmnopqrstuvwxyz' password=supersecretvalue"
    redacted = redact_text(text)
    assert 'sk-abcdefghijklmnopqrstuvwxyz' not in redacted
    assert 'supersecretvalue' not in redacted
    assert '[REDACTED_SECRET]' in redacted
