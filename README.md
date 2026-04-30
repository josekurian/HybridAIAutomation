# HybridAIAutomation

Version: `0.4.0`
Last updated: `2026-04-30`

Enterprise-grade AI automation starter platform for Oracle ERP and healthcare
customer POCs.

## POCs

- Invoice Processing Agent for finance and Oracle ERP-style AP flows
- Prior Authorization Agent for healthcare utilization and Oracle Health-style workflows

## Architecture

- OCI-first infrastructure assets
- OpenAI-ready orchestration with deterministic local fallback
- FastAPI backend with workflow execution, auth, and audit APIs
- React frontend with explainable workflow output
- RAG-style domain context for finance and healthcare rules

## Quick Start

1. Copy `.env.example` to `.env`
2. Start the stack:

   ```bash
   docker-compose up --build
   ```

3. Open:

   - Frontend: `http://localhost:5401`
   - Backend docs: `http://localhost:5405/docs`
   - Health check: `http://localhost:5405/health`

## Local Development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 5405
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## What This Starter Demonstrates

- named workflow execution for each POC
- explainable routing decisions and next actions
- mocked Oracle ERP and Oracle Health handoff artifacts
- audit event creation for every workflow run
- optional token-based auth baseline for controlled demos

## Deployment

- OCI Terraform starter: `infrastructure/terraform/oci`
- Kubernetes / OKE starter: `infrastructure/kubernetes`
- Docker Compose local pilot environment: `docker-compose.yml`

## Documentation

- [Documentation Index](./docs/README.md)
- [Architecture Overview](./docs/architecture.md)
- [Repository Structure Guide](./docs/repository-structure.md)
- [Invoice Workflow Guide](./docs/workflows/invoice-processing.md)
- [Prior Authorization Workflow Guide](./docs/workflows/prior-authorization.md)
- [Customer POC Playbook](./docs/customer-poc-playbook.md)

## Repository Structure

- `backend/`: FastAPI app, agents, workflows, orchestration, integrations, and audit services
- `frontend/`: React/Vite operator console and studio UI
- `docs/`: architecture, delivery, and workflow documentation
- `infrastructure/`: OCI Terraform and Kubernetes starters
- `tests/`: API smoke tests
- `workflows/`: business workflow definitions

## Quality Gates

Local verification commands:

```bash
make test
make frontend-build
make compose-config
```

Full local verification:

```bash
make verify
```

Shell-based fallback when `make` is unavailable or blocked by local machine
tooling:

```bash
bash scripts/verify_local.sh
```

GitHub Actions CI now validates:

- backend tests
- frontend production build
- Docker Compose configuration and container builds

## Version 0.4.0 focus

This revision expands the documentation and architectural guidance using three
inputs reviewed on April 29, 2026:

- the current `HybridAIAutomation` starter implementation
- reusable AI automation libraries already present under `/Users/josekurian/AIAgents`
- current OpenAI and Oracle AI platform updates relevant to MCP, agent teams,
  workflow execution, and enterprise AI deployment

## Reuse priorities from local AI libraries

The highest-value assets already available locally are:

1. `AIAgents/AIAgentProjects/MCPPlatform`
2. `AIAgents/MCPEngine`
3. `AIAgents/EnterpriseAgents`
4. `AIAgents/OracleFinancialsFrontierFullImplementation`
5. `AIAgents/AIAgentProjects/EnterpriseAgents/oracle_health`

What each one should contribute here:

- `MCPPlatform`: shared MCP server registry, project overlays, aliases, and
  per-project allowlists
- `MCPEngine`: stronger auth, policy, approval, replay protection, and durable
  audit patterns
- `EnterpriseAgents`: reusable cross-domain agent and workflow contracts
- `OracleFinancialsFrontierFullImplementation`: Oracle Fusion finance workflow
  packs, typed tool contracts, model-routing patterns, and scorecard traces
- `oracle_health`: prior-auth and revenue-cycle workflow catalogs that are much
  broader than the current healthcare starter

## Latest platform implications

OpenAI and Oracle changes reviewed as of `2026-04-29` materially expand what
this repo can support next:

- OpenAI now documents remote MCP servers and connectors as first-class tools in
  the Responses API, which aligns directly with the local `MCPPlatform` reuse
  path.
- OpenAI's April 2026 model and platform updates make the Responses API the
  correct center of gravity for tool use, structured outputs, deep research, and
  background workflows.
- Oracle AI Agent Studio updates from March and April 2026 move beyond single
  agents into agentic applications, workflow orchestration, contextual memory,
  ROI measurement, and reusable agent teams.
- OCI Enterprise AI reached GA on March 31, 2026 with an OpenAI
  Responses-compatible API surface, tool calling, vector stores, and remote MCP
  calling, which reduces integration friction for an OCI-first deployment path.

## Roadmap

- Phase 1: Local MVP and internal demo readiness
- Phase 2: Customer pilots with Oracle and healthcare mock integrations
- Phase 3: Multi-tenant platform features, audit hardening, and auth expansion
- Phase 4: Production OCI deployment with real ERP, FHIR, and vector services

## Next Steps

- connect real OCR and document ingestion
- replace mocked Oracle handoffs with service adapters
- add persistent storage for cases, approvals, and audit analytics
- replace in-memory retrieval with a true vector-backed knowledge layer
- add customer-specific onboarding templates and security controls
