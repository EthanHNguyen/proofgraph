# ProofGraph

**Map what your system proves.**

ProofGraph scans local repos and evidence folders, uses agents to build cited security-control evidence graphs, and compiles reviewer-ready artifacts from validated claims and gaps.

ProofGraph is terminal-first, local-file oriented, and fail-closed: unsupported implementation claims become gaps or reviewer questions, not compliance language.

## What it produces

```text
out/
  control-map.json
  control-map.md
  poam.csv
  evidence-index.csv
  reviewer-questions.md
  controls/
    AC-2.md
    AU-6.md
    ...
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Quickstart

Run the synthetic sample with the offline semantic provider:

```bash
proofgraph map --profile starter --repo examples/sample-repo --out out --provider offline
proofgraph validate out/control-map.json
proofgraph explain AU-6 --from out/control-map.json
```

## Configure an agent provider

For production semantic mapping, configure an agent provider:

```bash
export PROOFGRAPH_PROVIDER=openai
export PROOFGRAPH_API_KEY=your_key_here
export PROOFGRAPH_MODEL=gpt-4.1-mini
```

Then run:

```bash
proofgraph map --profile starter --repo /path/to/repo --evidence /path/to/evidence --out out
```

## Trust model

ProofGraph uses this architecture:

```text
local repo/evidence
  → inventory + chunking
  → candidate retrieval
  → agent semantic mapper
  → deterministic validator
  → JSON evidence graph
  → markdown/csv artifacts
```

The agent may reason, but only validated, cited claims survive.

ProofGraph does **not** certify compliance, authorization, or audit readiness. It reports what cited evidence supports, what is partial, and what is missing.

## Starter controls

The starter profile includes AC-2, AU-2, AU-6, AU-12, CM-2, CM-6, CM-8, IA-2, RA-5, SC-7, SC-13, SI-4, and SI-7.

## Development

```bash
pytest
```

## Security and privacy

- Default workflow scans local files.
- Only candidate chunks for a control are sent to a configured remote provider.
- `.git`, `node_modules`, build outputs, virtualenvs, and vendored dirs are skipped.
- Do not commit real API keys. Use `.env.example` as a placeholder template.
