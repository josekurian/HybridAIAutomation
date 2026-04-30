# Documentation Index

Version: `0.4.0`
Last updated: `2026-04-30`

This directory documents the current starter implementation in two layers:

- Project phases: how the platform is assembled, how requests move through the
  runtime, and how the local deployment is validated.
- Workflow phases: how each business flow is broken into explicit steps, routing
  decisions, and escalation points.

## Recommended reading order

1. [Architecture Overview](./architecture.md)
2. [Repository Structure Guide](./repository-structure.md)
3. [Phase 1: Foundation and Bootstrap](./phases/phase-1-foundation-and-bootstrap.md)
4. [Phase 2: Request Intake and Routing](./phases/phase-2-request-intake-and-routing.md)
5. [Phase 3: Retrieval and Domain Analysis](./phases/phase-3-retrieval-and-domain-analysis.md)
6. [Phase 4: AI Enrichment and Fallback](./phases/phase-4-ai-enrichment-and-fallback.md)
7. [Phase 5: Frontend Operator Console](./phases/phase-5-frontend-operator-console.md)
8. [Phase 6: Deployment, Validation, and Extension](./phases/phase-6-deployment-validation-and-extension.md)
9. [Invoice Workflow Guide](./workflows/invoice-processing.md)
10. [Prior Authorization Workflow Guide](./workflows/prior-authorization.md)
11. [Customer POC Playbook](./customer-poc-playbook.md)

## Documentation map

| Document | Purpose |
| --- | --- |
| `architecture.md` | High-level component map, runtime path, and deployment view |
| `repository-structure.md` | Detailed directory-by-directory guide for backend, frontend, infrastructure, and CI |
| `phases/` | Project lifecycle and request-processing phases |
| `workflows/` | Step-by-step business workflow execution notes |
| `customer-poc-playbook.md` | Delivery, demo, and expansion guidance for new customer pilots |

## Revision 0.4.0 additions

This documentation revision adds four kinds of detail:

- versioned document control across the existing project docs
- reuse guidance based on the existing `/Users/josekurian/AIAgents` portfolio
- explicit mapping to MCP servers, Oracle Fusion AI agents, and Oracle AI Agent
  Studio workflow assets already developed in other local projects
- dated OpenAI and Oracle platform update guidance current as of `2026-04-29`

## Key findings from the local portfolio review

The strongest reuse opportunities came from:

- `AIAgents/AIAgentProjects/MCPPlatform`
- `AIAgents/MCPEngine`
- `AIAgents/EnterpriseAgents`
- `AIAgents/OracleFinancialsFrontierFullImplementation`
- `AIAgents/AIAgentProjects/EnterpriseAgents/oracle_health`

Important inventory signals:

- `AIAgents/docs/AI_AGENTS_AND_WORKFLOWS_PROJECT_INVENTORY_2026-04-10.md`
  reports `1156` agent entries and `279` workflow entries across the local
  portfolio.
- `AIAgents/docs/AI_AGENT_TEAMS_PROJECT_INVENTORY_AND_RECOMMENDATIONS_2026-04-28.md`
  identifies `18` explicit runtime teams and `20` workflow-defined team
  compositions already available for reuse or adaptation.

## Recommended reading for the new material

1. [Architecture Overview](./architecture.md)
2. [Customer POC Playbook](./customer-poc-playbook.md)
3. the six phase guides in order
4. the workflow guides for invoice and prior authorization

## Scope note

These documents describe the repository as it exists today:

- FastAPI backend
- React/Vite frontend
- Deterministic local extraction
- Optional OpenAI and OCI summary layers
- Docker Compose, OCI Terraform, and Kubernetes starter assets

They also call out where the implementation is intentionally a starter and where
production hardening still needs to be added.
