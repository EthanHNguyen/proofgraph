from __future__ import annotations

import json
import os
import re
import urllib.request
from abc import ABC, abstractmethod

from proofgraph.schemas import AgentClaim, AgentControlResult, AgentGap, Control, ControlStatus, EvidenceChunk
from proofgraph.redaction import redact_text

SYSTEM_RULES = [
    "Every positive claim must cite one or more chunk IDs.",
    "Do not claim compliance, authorization, certification, or audit readiness.",
    "Use partial/gap/unknown when evidence is incomplete.",
    "Return only JSON matching the schema.",
]


class AgentProvider(ABC):
    @abstractmethod
    def map_control(self, control: Control, candidate_chunks: list[EvidenceChunk]) -> AgentControlResult:
        raise NotImplementedError


def build_agent_payload(control: Control, candidate_chunks: list[EvidenceChunk]) -> dict:
    return {
        "control": control.model_dump(),
        "candidate_chunks": [
            {
                "id": chunk.id,
                "path": chunk.path,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "kind": chunk.kind.value,
                "text": redact_text(chunk.text),
            }
            for chunk in candidate_chunks
        ],
        "rules": SYSTEM_RULES,
        "output_schema": {
            "control_id": control.id,
            "status": "supported | partial | gap | unknown",
            "claims": [{"statement": "string", "evidence_refs": ["EV-0001"], "confidence": "high | medium | low"}],
            "gaps": [{"statement": "string", "reason": "string", "recommended_action": "string"}],
            "reviewer_questions": ["string"],
        },
    }


def parse_agent_json(text: str) -> AgentControlResult:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
    return AgentControlResult.model_validate(json.loads(cleaned))


class OpenAIAgentProvider(AgentProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv('PROOFGRAPH_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.model = model or os.getenv('PROOFGRAPH_MODEL', 'gpt-4.1-mini')
        if not self.api_key:
            raise RuntimeError('PROOFGRAPH_API_KEY or OPENAI_API_KEY is required for openai provider')

    def map_control(self, control: Control, candidate_chunks: list[EvidenceChunk]) -> AgentControlResult:
        payload = build_agent_payload(control, candidate_chunks)
        prompt = (
            "You are ProofGraph's semantic security evidence indexer. "
            "Map evidence chunks to one security control. Return only strict JSON.\n\n"
            + json.dumps(payload, indent=2)
        )
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only JSON. Cite every positive claim by evidence chunk id. Do not claim compliance."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=body,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode('utf-8'))
        return parse_agent_json(data['choices'][0]['message']['content'])


class OfflineSemanticAgentProvider(AgentProvider):
    """Development fallback that behaves like a constrained semantic fact emitter.

    This is not the product's authority; it exists so the sample/eval suite and CLI
    can run without external credentials. Production use should configure OpenAI or
    another provider.
    """
    def map_control(self, control: Control, candidate_chunks: list[EvidenceChunk]) -> AgentControlResult:
        joined = "\n".join(f"[{c.id}] {c.path}\n{c.text}" for c in candidate_chunks).lower()
        claims: list[AgentClaim] = []
        gaps: list[AgentGap] = []
        questions: list[str] = []

        def refs_containing(*needles: str) -> list[str]:
            refs = []
            for chunk in candidate_chunks:
                txt = f"{chunk.path}\n{chunk.text}".lower()
                if any(n in txt for n in needles):
                    refs.append(chunk.id)
            return refs[:3]

        cid = control.id
        if cid == 'AU-6':
            refs = refs_containing('audit_event', 'audit event', 'audit logger', 'cloudtrail')
            field_refs = refs_containing('actor', 'action', 'target', 'timestamp')
            if refs:
                claims.append(AgentClaim(statement='Privileged or security-relevant actions emit audit events.', evidence_refs=refs, confidence='high'))
            if field_refs and all(term in joined for term in ['actor', 'action']) and ('target' in joined or 'resource' in joined) and ('timestamp' in joined or 'time' in joined):
                claims.append(AgentClaim(statement='Audit evidence includes actor, action, target or resource, and timestamp context.', evidence_refs=field_refs, confidence='high'))
            if not refs_containing('retention', 'retention_in_days'):
                gaps.append(AgentGap(statement='No cited evidence defines audit log retention.', reason='No candidate chunk identifies retention period or lifecycle policy.', recommended_action='Provide logging retention configuration or policy evidence.'))
            if not refs_containing('review cadence', 'weekly review', 'monthly review', 'designated reviewer'):
                gaps.append(AgentGap(statement='No cited evidence defines audit log review cadence.', reason='No candidate chunk identifies reviewer role, frequency, or review records.', recommended_action='Provide review runbook or review records.'))
            questions.append('Who reviews privileged action logs and where are review records stored?')
        elif cid == 'AU-12':
            refs = refs_containing('audit_event', 'cloudtrail', 'audit logger')
            if refs:
                claims.append(AgentClaim(statement='The system generates audit records for security-relevant events.', evidence_refs=refs, confidence='high'))
            else:
                gaps.append(AgentGap(statement='No cited evidence shows audit record generation.', reason='No audit generation source/config found.', recommended_action='Provide source or platform audit-generation evidence.'))
        elif cid == 'AU-2':
            refs = refs_containing('auditable event', 'event_type', 'authentication failure', 'role_change')
            if refs:
                claims.append(AgentClaim(statement='The evidence identifies security-relevant auditable event types.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence identifies auditable event types.', reason='No event selection evidence found.', recommended_action='Provide event logging policy or implementation evidence.'))
        elif cid == 'IA-2':
            refs = refs_containing('mfa', 'multi-factor', 'require_mfa', 'identity provider', 'principal', 'session_user')
            if refs:
                claims.append(AgentClaim(statement='The evidence shows user or principal authentication controls.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence shows user identification and authentication controls.', reason='No identity/MFA evidence found.', recommended_action='Provide auth middleware, IdP policy, or MFA configuration evidence.'))
        elif cid == 'AC-2':
            refs = refs_containing('create_user', 'disable_user', 'account review', 'stale users', 'access review')
            if refs:
                claims.append(AgentClaim(statement='The evidence shows account lifecycle or account review activity.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence shows account lifecycle management.', reason='No provisioning, disablement, or review evidence found.', recommended_action='Provide account lifecycle workflow evidence.'))
        elif cid == 'CM-6':
            neg = 'encryption is not implemented' in joined or 'not currently implemented' in joined
            refs = refs_containing('tls', 'encryption', 'password_policy', 'ssh_root_login', 'hardened')
            if refs and not neg:
                claims.append(AgentClaim(statement='The evidence defines secure configuration settings.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence proves secure configuration settings are implemented.', reason='No positive secure setting evidence found or evidence is explicitly negative.', recommended_action='Provide secure configuration/IaC evidence.'))
        elif cid == 'CM-2':
            refs = refs_containing('configuration_baseline', 'approved baseline', 'golden image')
            if refs:
                claims.append(AgentClaim(statement='The evidence identifies a configuration baseline.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence identifies an approved configuration baseline.', reason='No baseline configuration evidence found.', recommended_action='Provide baseline config artifact.'))
        elif cid == 'CM-8':
            refs = refs_containing('component inventory', 'asset inventory', 'service_owner', 'image_tag', 'deployed resources')
            if refs:
                claims.append(AgentClaim(statement='The evidence identifies system components or inventory metadata.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence identifies system component inventory.', reason='No component/asset inventory evidence found.', recommended_action='Provide component inventory evidence.'))
        elif cid == 'SC-7':
            refs = refs_containing('ingress', 'egress', 'security_group', 'firewall', 'allowed_ports', 'cidr')
            if refs:
                claims.append(AgentClaim(statement='The evidence defines boundary interfaces or traffic restrictions.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence defines boundary protection rules.', reason='No ingress/egress/firewall/security-group evidence found.', recommended_action='Provide boundary/IaC evidence.'))
        elif cid == 'SC-13':
            neg = 'encryption is not implemented' in joined
            refs = refs_containing('tls', 'kms', 'cipher', 'certificate', 'https', 'encryption')
            if refs and not neg:
                claims.append(AgentClaim(statement='The evidence identifies cryptographic protection mechanisms.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence proves cryptographic protection is configured.', reason='No positive crypto evidence found.', recommended_action='Provide TLS/KMS/certificate configuration evidence.'))
        elif cid == 'SI-4':
            refs = refs_containing('alert', 'detection', 'security monitoring', 'siem', 'on-call', 'incident')
            if refs:
                claims.append(AgentClaim(statement='The evidence defines security monitoring or alerting.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence defines security monitoring or alerting.', reason='No detection/alert evidence found.', recommended_action='Provide monitoring config or runbook evidence.'))
        elif cid == 'RA-5':
            refs = refs_containing('trivy', 'snyk', 'dependabot', 'vulnerability scan', 'container scan')
            if refs:
                claims.append(AgentClaim(statement='The evidence identifies vulnerability or dependency scanning.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence identifies vulnerability scanning.', reason='No scanner config or results found.', recommended_action='Provide vulnerability scanning evidence.'))
        elif cid == 'SI-7':
            refs = refs_containing('checksum', 'signature', 'signed image', 'provenance', 'slsa', 'verify artifact')
            if refs:
                claims.append(AgentClaim(statement='The evidence identifies integrity verification for artifacts or software.', evidence_refs=refs, confidence='medium'))
            else:
                gaps.append(AgentGap(statement='No cited evidence identifies software/information integrity checks.', reason='No signature/checksum/provenance evidence found.', recommended_action='Provide artifact integrity evidence.'))
        else:
            gaps.append(AgentGap(statement=f'No semantic mapper behavior available for {cid}.', reason='Unsupported control in offline provider.', recommended_action='Use a configured agent provider or add profile-specific evaluation guidance.'))

        status = ControlStatus.supported if claims and not gaps else ControlStatus.partial if claims else ControlStatus.gap
        if not questions:
            questions.append(f'What evidence should a reviewer inspect for {cid}?')
        return AgentControlResult(control_id=cid, status=status, claims=claims, gaps=gaps, reviewer_questions=questions)


def get_provider(name: str | None = None) -> AgentProvider:
    provider = (name or os.getenv('PROOFGRAPH_PROVIDER') or 'offline').lower()
    if provider == 'openai':
        return OpenAIAgentProvider()
    if provider in {'offline', 'fixture', 'mock'}:
        return OfflineSemanticAgentProvider()
    raise ValueError(f'unknown provider: {provider}')
