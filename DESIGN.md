# ProofGraph: Agent-Built Security Evidence Graph

**Status:** Draft  
**Author:** Ethan Nguyen / Hermes  
**Created:** 2026-04-30  
**Target repo:** `proofgraph`  
**Audience:** Engineering, security/compliance product reviewers, future coding agents

---

## 1. Summary

ProofGraph (`proofgraph`) is a terminal-first tool that scans a local repo or evidence folder, maps source/config/document evidence to a selected security-control profile, builds a source-backed evidence graph, and renders reviewer-facing artifacts.

The key design decision is that **an agent builds semantic graph facts** because security-control evidence mapping is not reliably expressible as keyword matching. Deterministic code handles corpus inventory, chunking, schema validation, graph import, and artifact rendering.

Core invariant:

> The agent may reason, but only validated, cited claims survive into the graph and generated artifacts.

Primary command:

```bash
proofgraph map --profile profiles/starter.yaml --evidence ./evidence --repo ./repo --out ./proofgraph-out
```

Primary outputs:

```text
proofgraph-out/
  control-map.json
  control-map.md
  poam.csv
  evidence-index.csv
  reviewer-questions.md
  controls/
    AC-2.md
    AU-2.md
    AU-6.md
    ...
```

---

## 2. Background

Security/compliance artifact generation is often blocked by evidence archaeology. Engineers know system behavior lives in source code, infrastructure config, CI/CD workflows, cloud policy, logs, and runbooks, but compliance workflows require control-oriented outputs: implementation statements, evidence indexes, reviewer questions, and POA&M gaps.

Existing graph prior art such as Sourcegraph/SCIP, Kythe, GitHub Stack Graphs, and `sckg/sckg` suggests a useful pattern:

```text
corpus ingestion
  → semantic indexing
  → typed facts / graph IR
  → validation/import
  → query or artifact rendering
```

Sourcegraph uses compiler/typechecker/LSP-backed indexers to emit code-intelligence facts. Compliance evidence has no equivalent compiler. Therefore, `proofgraph` uses an agent as the semantic indexer, constrained to emit typed graph facts with citations.

---

## 3. Problem Statement

Given a local repo or evidence folder and a selected security-control profile, produce a source-backed map from evidence to controls and generate practical artifacts:

- control implementation summaries
- per-control evidence citations
- missing evidence gaps
- POA&M rows
- evidence index
- reviewer questions

The system must avoid unsupported compliance language. It should not say a system is compliant, authorized, audit-ready, or FedRAMP-ready. It should say what cited evidence supports, what is partial, and what is missing.

---

## 4. Goals

### G1. Terminal-first local workflow

`proofgraph` must run from a terminal against local files without a web UI.

### G2. Agent-built semantic graph

The mapper must use an agent to interpret evidence semantics and emit graph facts. Keyword matching may retrieve candidate chunks but must not determine final support.

### G3. Source-backed claims only

Every positive claim must cite one or more evidence chunks with stable IDs, paths, line ranges, hashes, and excerpts.

### G4. Fail closed

When evidence is missing, ambiguous, or weak, the system must emit `gap`, `partial`, or `unknown`, not supported implementation language.

### G5. Profile-scoped control coverage

“All relevant controls” means all controls selected by a named profile/baseline, not the full NIST 800-53 catalog.

### G6. Artifact outputs from graph

Markdown, CSV, and JSON artifacts must render from the validated graph, not directly from raw agent prose.

### G7. Debuggable per-control execution

Users must be able to run/debug mapping for a single control.

---

## 5. Non-Goals

- No web UI.
- No hosted SaaS service.
- No graph database in MVP.
- No vector database dependency in MVP.
- No full NIST/FedRAMP catalog ingestion in MVP.
- No cloud API evidence collection in MVP.
- No Jira/GRC/OSCAL/TELOS integration in MVP.
- No compliance certification or authorization assertions.
- No autonomous remediation.
- No continuous monitoring.
- No direct repo-to-SSP prose generation without graph validation.

---

## 6. User Experience

### 6.1 Map full profile

```bash
proofgraph map \
  --profile profiles/starter.yaml \
  --repo ./my-service \
  --evidence ./evidence \
  --out ./proofgraph-out
```

Example terminal output:

```text
ProofGraph

Profile: starter-security-profile
Repo: ./my-service
Evidence: ./evidence
Controls selected: 13
Files scanned: 184
Evidence chunks: 912

Mapping controls with semantic agent:
  AC-2   partial    2 claims, 3 gaps
  AU-2   partial    3 claims, 1 gap
  AU-6   partial    2 claims, 2 gaps
  AU-12  supported  2 claims, 0 gaps
  CM-2   gap        0 claims, 2 gaps
  ...

Artifacts written:
  proofgraph-out/control-map.json
  proofgraph-out/control-map.md
  proofgraph-out/poam.csv
  proofgraph-out/evidence-index.csv
  proofgraph-out/reviewer-questions.md
  proofgraph-out/controls/*.md
```

### 6.2 Map one control

```bash
proofgraph map-control AU-6 --profile profiles/starter.yaml --repo ./my-service --out ./proofgraph-out
```

### 6.3 Explain one control from a graph

```bash
proofgraph explain AU-6 --from ./proofgraph-out/control-map.json
```

Example:

```text
AU-6 Audit Record Review, Analysis, and Reporting
Status: partial

Supported claims:
  ✓ Privileged role changes emit audit events.
    - app/admin.py:41-58 hash abc123

Missing evidence:
  ✕ No cited evidence defines audit log review cadence.
  ✕ No cited evidence defines audit log retention.

Reviewer questions:
  - Who reviews privileged action logs and where are records stored?
```

### 6.4 Validate graph

```bash
proofgraph validate ./proofgraph-out/control-map.json
```

---

## 7. Starter Profile Scope

MVP profile: `starter-security-profile`.

Controls:

```text
AC-2   Account Management
AU-2   Event Logging
AU-6   Audit Review, Analysis, and Reporting
AU-12  Audit Record Generation
CM-2   Baseline Configuration
CM-6   Configuration Settings
CM-8   System Component Inventory
IA-2   Identification and Authentication
RA-5   Vulnerability Monitoring and Scanning
SC-7   Boundary Protection
SC-13  Cryptographic Protection
SI-4   System Monitoring
SI-7   Software/Firmware/Information Integrity
```

Rationale:

- These controls are likely to have repo/config/IaC evidence.
- They cover identity, accounts, logging, configuration, inventory, boundary, crypto, vulnerability scanning, and monitoring.
- They avoid controls that are primarily organizational, personnel, physical, or policy-only.

---

## 8. High-Level Architecture

```text
local repo/evidence folder
        +
selected control profile
        │
        ▼
┌──────────────────────┐
│ Inventory + Chunking │ deterministic
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Candidate Retrieval  │ deterministic helper only
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Agent Semantic Mapper│ emits typed graph facts
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Validation + Import  │ deterministic fail-closed gate
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Evidence Graph JSON  │ canonical state
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Artifact Renderers   │ deterministic markdown/csv/json
└──────────────────────┘
```

---

## 9. Repository Structure

```text
proofgraph/
  pyproject.toml
  README.md
  DESIGN.md
  cam/
    __init__.py
    cli.py
    profiles.py
    inventory.py
    chunking.py
    retrieval.py
    agent_mapper.py
    schemas.py
    validate.py
    graph.py
    export/
      __init__.py
      json_export.py
      markdown_export.py
      csv_export.py
  profiles/
    starter.yaml
  examples/
    sample-repo/
      app/
      infra/
      docs/
  tests/
    test_profiles.py
    test_inventory.py
    test_retrieval.py
    test_agent_mapper.py
    test_validate.py
    test_graph.py
    test_export.py
    test_cli.py
```

---

## 10. Data Model

### 10.1 EvidenceSource

Represents a scanned file.

```json
{
  "id": "SRC-0001",
  "path": "app/admin.py",
  "kind": "source",
  "sha256": "...",
  "size_bytes": 2048
}
```

### 10.2 EvidenceChunk

Represents a cited line-aware text chunk.

```json
{
  "id": "EV-0001",
  "source_id": "SRC-0001",
  "path": "app/admin.py",
  "line_start": 41,
  "line_end": 58,
  "sha256": "...",
  "text": "audit_event('role_change', actor=actor, action='assign_role', target=target, timestamp=now())"
}
```

### 10.3 Control

```json
{
  "id": "AU-6",
  "title": "Audit Record Review, Analysis, and Reporting",
  "objective": "Determine whether audit records are reviewed, analyzed, and reported using source-backed evidence.",
  "evidence_hints": ["audit event generation", "log review", "retention", "SIEM"]
}
```

### 10.4 Claim

```json
{
  "id": "CLAIM-AU6-001",
  "control_id": "AU-6",
  "statement": "Privileged role changes emit audit events.",
  "confidence": "high",
  "evidence_refs": ["EV-0001"]
}
```

### 10.5 Gap

```json
{
  "id": "GAP-AU6-001",
  "control_id": "AU-6",
  "statement": "No cited evidence defines audit log review cadence.",
  "reason": "Candidate evidence did not identify reviewer role, frequency, or review records.",
  "recommended_action": "Provide log review procedure or review records."
}
```

### 10.6 GraphEdge

```json
{
  "from": "EV-0001",
  "to": "CLAIM-AU6-001",
  "type": "supports"
}
```

Additional edge:

```json
{
  "from": "CLAIM-AU6-001",
  "to": "AU-6",
  "type": "supports"
}
```

Gap edge:

```json
{
  "from": "GAP-AU6-001",
  "to": "AU-6",
  "type": "missing_for"
}
```

### 10.7 ControlEvidenceGraph

Canonical output.

```json
{
  "schema_version": "0.1",
  "profile_id": "starter-security-profile",
  "generated_at": "2026-04-30T00:00:00Z",
  "controls": [],
  "sources": [],
  "chunks": [],
  "claims": [],
  "gaps": [],
  "reviewer_questions": [],
  "edges": [],
  "summary": {}
}
```

---

## 11. Control Profile Format

`profiles/starter.yaml`:

```yaml
id: starter-security-profile
name: Starter Security Profile
description: Terminal-first profile for source-backed artifact mapping.
controls:
  - id: AU-6
    title: Audit Record Review, Analysis, and Reporting
    objective: Determine whether audit records are reviewed, analyzed, and reported using source-backed evidence.
    evidence_hints:
      - audit event generation
      - privileged action logging
      - actor/action/target/timestamp fields
      - log review cadence
      - audit log retention
      - SIEM or centralized logging destination
    expected_evidence:
      - source
      - config
      - infrastructure
      - policy
      - runbook
```

Profiles select controls and describe objectives. Profiles do not hardcode final mappings.

---

## 12. Agent Mapper Design

### 12.1 Invocation Granularity

Run one semantic mapping pass per control:

```text
for control in selected_profile.controls:
  candidates = retrieve_candidates(control, chunks)
  facts = agent_map_control(control, candidates)
  validated = validate_facts(facts, candidates, graph)
  graph.import(validated)
```

Rationale:

- Smaller prompts.
- Easier retries.
- Easier debugging.
- One failed control does not corrupt the entire graph.
- Different controls can later use specialized prompts.

### 12.2 Agent Contract

Input:

```json
{
  "control": {
    "id": "AU-6",
    "title": "Audit Record Review, Analysis, and Reporting",
    "objective": "...",
    "evidence_hints": []
  },
  "candidate_chunks": [
    {
      "id": "EV-0001",
      "path": "app/admin.py",
      "line_start": 41,
      "line_end": 58,
      "text": "..."
    }
  ],
  "rules": [
    "Every positive claim must cite one or more chunk IDs.",
    "Do not claim compliance, authorization, certification, or audit readiness.",
    "Use partial/gap/unknown when evidence is incomplete.",
    "Return only JSON matching the schema."
  ]
}
```

Output:

```json
{
  "control_id": "AU-6",
  "status": "partial",
  "claims": [
    {
      "statement": "Privileged role changes emit audit events.",
      "evidence_refs": ["EV-0001"],
      "confidence": "high"
    }
  ],
  "gaps": [
    {
      "statement": "No cited evidence defines audit log review cadence.",
      "reason": "No candidate chunk identifies reviewer role, frequency, or review records.",
      "recommended_action": "Provide review runbook or records."
    }
  ],
  "reviewer_questions": [
    "Who reviews privileged action logs and where are review records stored?"
  ]
}
```

### 12.3 Prompt Rules

The mapper prompt must enforce:

- Emit JSON only.
- Use only candidate chunk IDs for evidence refs.
- Prefer narrower claims over broad claims.
- If evidence is policy-only, say policy evidence, not implementation evidence.
- If evidence is indirect, use `medium` or `low` confidence.
- Missing evidence must be represented as gaps/questions.
- Do not use banned compliance language.

---

## 13. Candidate Retrieval

Candidate retrieval is deterministic and used only to reduce context size.

Signals:

- control evidence hints
- control title/objective terms
- file path relevance (`infra/`, `security/`, `auth/`, `logging/`, `docs/`)
- file type priority (`.py`, `.ts`, `.tf`, `.yaml`, `.md`, `.log`)
- heading overlap in Markdown/YAML
- simple lexical overlap

Candidate retrieval is not authoritative. The agent decides semantic support; the validator gates claims.

MVP can use top `N=25` chunks per control.

---

## 14. Validation and Import

The validator is deterministic and strict.

Reject or downgrade when:

- output is not schema-valid JSON
- `control_id` is not selected by the profile
- claim has no `evidence_refs`
- an evidence ref does not exist
- evidence ref line range is invalid
- claim contains banned compliance/certification language
- claim states a broader fact than cited text reasonably supports
- status is `supported` while gaps exist
- agent invents files, controls, dates, tools, people, approvals, or review cadence

Banned terms include:

```text
compliant
certified
authorized
ATO-ready
audit-ready
meets FedRAMP
satisfies NIST
fully implemented
```

Permitted language:

```text
Evidence supports...
Evidence partially supports...
No cited evidence was found...
Requires human input...
```

If validation fails for a control, default behavior should be fail closed:

```json
{
  "control_id": "AU-6",
  "status": "unknown",
  "claims": [],
  "gaps": [
    {
      "statement": "Agent output failed validation; human review required.",
      "reason": "..."
    }
  ]
}
```

Optionally, CLI can expose `--strict` to exit nonzero on validation failure.

---

## 15. Artifact Generation

Artifacts are generated from the validated graph, not from raw agent prose.

### 15.1 `control-map.json`

Canonical graph.

### 15.2 `control-map.md`

Human summary table:

```markdown
# Control Artifact Map

| Control | Status | Claims | Gaps | Evidence |
|---|---:|---:|---:|---:|
| AC-2 | Partial | 2 | 3 | 4 |
| AU-6 | Partial | 2 | 2 | 3 |
```

### 15.3 `controls/{CONTROL_ID}.md`

Per-control implementation language.

Generated from template:

```markdown
# AU-6 Audit Record Review, Analysis, and Reporting

## Source-backed implementation language

Available evidence supports the following implementation statements:

- Privileged role changes emit audit events.
  - Evidence: `app/admin.py:41-58` hash `abc123`

## Evidence gaps / requires human input

- No cited evidence defines audit log review cadence.
- No cited evidence defines audit log retention.

## Reviewer questions

- Who reviews privileged action logs and where are records stored?
```

### 15.4 `poam.csv`

One row per concrete gap.

Columns:

```text
id,control_id,weakness,evidence_status,risk,recommended_action,evidence_needed,status,owner,target_date
```

### 15.5 `evidence-index.csv`

One row per cited evidence chunk.

Columns:

```text
evidence_id,path,line_start,line_end,sha256,kind,supports_claims,supports_controls,excerpt
```

### 15.6 `reviewer-questions.md`

Grouped by control.

---

## 16. Optional Language Polish

MVP uses deterministic templates.

A later `--polish` mode may use a second constrained language agent after graph validation:

```bash
proofgraph map --profile profiles/starter.yaml --repo ./repo --out ./out --polish
```

Polish agent input is the validated graph only. It must not see raw repo context except citations already in graph.

Rules:

- Use only validated claims, gaps, questions, and profile metadata.
- Do not introduce new facts.
- Preserve missing evidence.
- Avoid banned compliance language.
- Return JSON with traceability from sentences to claim/gap IDs.

If polish output fails validation, fall back to deterministic template output.

---

## 17. Error Handling

### Agent unavailable

Default:

```text
exit nonzero with clear error
```

Optional later flag:

```bash
--allow-agent-failure
```

would write unknown/gap controls instead of failing.

### Malformed profile

Exit nonzero before scanning.

### Empty evidence corpus

Produce graph with selected controls and gaps/questions only.

### Oversized files

Skip with warning and include skipped file summary.

### Unsupported files

Skip binary/unsupported types. Do not crash.

---

## 18. Security and Privacy

- Default execution is local.
- Do not send full repo by default if provider supports local model; otherwise clearly document provider boundary.
- Only candidate chunks for one control are sent to the agent provider.
- Do not persist raw prompts unless `--debug-prompts` is set.
- Do not log secrets found in files.
- Add redaction pass for common secret patterns before agent calls.
- `.git`, `node_modules`, build artifacts, and vendored dependencies are skipped by default.

---

## 19. Testing Strategy

### Unit tests

- profile parsing
- file inventory
- chunking
- retrieval scoring
- graph assembly
- validation rules
- markdown/csv rendering

### Integration tests

- full `proofgraph map` against `examples/sample-repo`
- single-control mapping
- empty evidence folder
- malformed profile
- agent output validation failure

### Agent/eval fixtures

Fixture cases:

1. Direct support: clear audit event code supports AU-6/AU-12.
2. Indirect support: docs mention logging but not review cadence.
3. Missing evidence: no MFA evidence for IA-2.
4. Misleading keyword: file says encryption is not implemented.
5. Control overlap: CloudTrail may relate to AU-2, AU-6, AU-12, SI-4 but requires distinct claims.
6. Compliance language trap: doc says “FedRAMP ready” without concrete evidence.
7. Policy-only evidence: policy statement exists but no implementation proof.

### Golden assertions

- every claim has evidence refs
- every evidence ref exists
- no banned language in artifacts
- all selected controls appear in graph
- no non-selected controls appear
- POA&M rows derive from gaps
- evidence index derives from cited chunks

---

## 20. Rollout Plan

### Phase 0: Skeleton

- Create repo and package.
- Add CLI shell.
- Add Pydantic schemas.
- Add starter profile.

Exit:

```bash
proofgraph --help
proofgraph profiles list
pytest
```

### Phase 1: Evidence inventory

- Recursive scan.
- Ignore rules.
- Line-aware chunking.
- Stable IDs/hashes.

Exit:

```bash
proofgraph inventory ./examples/sample-repo --out ./out
```

### Phase 2: Agent mapper for one control

- Implement `map-control`.
- Add agent provider abstraction.
- Add strict schema parser.
- Add validator.

Exit:

```bash
proofgraph map-control AU-6 --profile profiles/starter.yaml --repo ./examples/sample-repo --out ./out
```

### Phase 3: Full profile graph

- Iterate selected controls.
- Assemble graph.
- Add `proofgraph validate`.

Exit:

```bash
proofgraph map --profile profiles/starter.yaml --repo ./examples/sample-repo --out ./out
proofgraph validate ./out/control-map.json
```

### Phase 4: Artifacts

- Render markdown/csv/json outputs.
- Add `proofgraph explain`.

Exit:

```bash
ls out/
proofgraph explain AU-6 --from out/control-map.json
```

### Phase 5: Hardening

- Add eval fixtures.
- Add banned language checks.
- Add redaction.
- Add README quickstart.

---

## 21. Alternatives Considered

### A1. Keyword/profile scanner only

Rejected. Keyword matching is insufficient for semantic evidence mapping and would produce false positives/negatives.

### A2. Agent directly drafts artifacts

Rejected. This collapses evidence mapping and prose generation, making hallucinated control language more likely.

### A3. Graph database in MVP

Rejected. JSON graph is enough. Neo4j/RDF/SPARQL introduces infrastructure before product value is proven.

### A4. Full public control knowledge graph first

Rejected for MVP. `sckg/sckg`-style mappings are useful later, but the immediate wedge is private system evidence to controls.

### A5. One giant repo-level agent pass

Rejected. Hard to debug, expensive, unstable, and likely to lose per-control nuance.

---

## 22. Open Questions

1. Which model/provider should be the default agent backend?
2. Should v0 require an API key, or support a local model path first?
3. Should `--strict` be default for validation failure?
4. How aggressively should secret redaction skip or mask candidate chunks?
5. Should profiles be YAML only, or support JSON too?
6. What is the minimal sample repo that demonstrates all 13 controls without feeling artificial?
7. Do we include policy/runbook evidence in the sample or focus on source/IaC first?

---

## 23. Decision Summary

- Build a separate terminal-first repo: `proofgraph`.
- Use an agent as the semantic graph fact emitter.
- Use deterministic inventory, validation, graph import, and rendering.
- Use JSON graph as canonical output.
- Generate artifacts from validated graph only.
- Start with a selected starter profile, not all NIST controls.
- Do not build UI or graph database in MVP.

Final architecture:

```text
agent for judgment
schemas for structure
validators for trust
JSON graph for canonical state
renderers for artifacts
```
