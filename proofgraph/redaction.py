from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*["\']?[^"\'\s]{8,}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'sk-[A-Za-z0-9_-]{20,}'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.DOTALL),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub('[REDACTED_SECRET]', redacted)
    return redacted
