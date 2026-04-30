# ProofGraph

**Map what your system proves.**

ProofGraph is a terminal-first CLI that turns a local repo or evidence folder into a source-cited security-control evidence graph, then renders reviewer-friendly Markdown, JSON, and CSV artifacts.

It is built around one rule:

> The agent may reason, but only validated, cited claims survive.

ProofGraph uses an agent/provider abstraction for semantic evidence judgment, deterministic validators for trust boundaries, and a JSON graph as canonical state. Keyword matching is only used to narrow candidate evidence.

## Quick start

```bash
git clone https://github.com/EthanHNguyen/proofgraph.git
cd proofgraph
python -m venv .venv
source .venv/bin/activate
pip install -e .
proofgraph demo
```

That writes artifacts to:

```text
proofgraph-out/
  control-map.json
  control-map.md
  evidence-index.csv
  poam.csv
  reviewer-questions.md
  controls/
    AC-2.md
    AU-2.md
    AU-6.md
    ...
```

## One command for your repo

```bash
proofgraph run /path/to/your/repo
```

Optional evidence folder:

```bash
proofgraph run /path/to/your/repo --evidence /path/to/evidence
```

Custom output directory:

```bash
proofgraph run /path/to/your/repo --out review-pack
```

## Core commands

| Goal | Command |
|---|---|
| Run the synthetic sample | `proofgraph demo` |
| Map + validate a repo | `proofgraph run /path/to/repo` |
| Map without validation wrapper | `proofgraph map /path/to/repo` |
| Explain one control | `proofgraph explain AU-6 --from proofgraph-out/control-map.json` |
| Validate a graph | `proofgraph validate proofgraph-out/control-map.json` |
| Show starter controls | `proofgraph profiles show starter` |
| Map one control | `proofgraph map-control AU-6 /path/to/repo` |

The short path is:

```bash
proofgraph run .
```

## Agent providers

The default provider is `offline`, which lets the sample and tests run without credentials.

For semantic mapping with OpenAI:

```bash
export PROOFGRAPH_PROVIDER=openai
read -rsp "PROOFGRAPH_API_KEY: " PROOFGRAPH_API_KEY && export PROOFGRAPH_API_KEY
export PROOFGRAPH_MODEL="gpt-4.1-mini"

proofgraph run /path/to/repo --evidence /path/to/evidence
```

You can also pass the provider explicitly:

```bash
proofgraph run /path/to/repo --provider openai
```

## What ProofGraph produces

ProofGraph emits a validated evidence graph and reviewer-facing artifacts:

- `control-map.json` — canonical graph state
- `control-map.md` — profile-level summary
- `controls/*.md` — per-control evidence pages
- `evidence-index.csv` — cited evidence inventory
- `poam.csv` — gap/action tracker
- `reviewer-questions.md` — unresolved reviewer questions

Each positive claim must cite evidence chunks with file paths, line ranges, and content hashes.

## Starter profile

The bundled starter profile includes 13 controls:

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
SI-7   Software, Firmware, and Information Integrity
```

## Trust model

```text
local repo/evidence
  → inventory + chunking
  → candidate retrieval
  → agent semantic mapper
  → deterministic validator
  → JSON evidence graph
  → Markdown/CSV artifacts
```

Trust boundaries:

- Local files are chunked with stable IDs and hashes.
- Candidate retrieval narrows context only; it does not decide support.
- Agent/provider output is treated as untrusted until validated.
- Positive claims require valid evidence references.
- Missing or weak evidence becomes gaps or reviewer questions.
- Secret-like strings are redacted before candidate text is sent to a remote provider.
- Symlinked files are skipped during inventory.

ProofGraph is not an official determination system. It helps reviewers see what local evidence supports and where evidence is missing.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Smoke test:

```bash
proofgraph demo --out /tmp/proofgraph-demo
proofgraph validate /tmp/proofgraph-demo/control-map.json
proofgraph explain AU-6 --from /tmp/proofgraph-demo/control-map.json
```

## Repository safety

- Do not commit `.env`, `.env.local`, credentials, or real evidence exports.
- `.git`, `.venv`, `node_modules`, build outputs, and generated output directories are skipped or ignored.
- The bundled sample is synthetic demo evidence.
