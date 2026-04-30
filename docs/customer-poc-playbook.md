# Customer POC Playbook

Version: `0.4.0`
Last updated: `2026-04-29`

## Objective

Use this repository not only as an engineering starter, but as a repeatable
delivery package for new customer POCs in finance and healthcare.

## What customers usually need to see

For a pilot to convert, the customer usually needs evidence in four areas:

1. Business relevance
2. Explainability
3. Integration readiness
4. Operational control

This starter now supports all four at a baseline level.

## POC success pattern

### Phase 1: Discovery and scoping

Capture these before building customer-specific features:

- target business process
- document types and sample volume
- source systems
- approval thresholds
- compliance constraints
- pilot success criteria

Output:

- one-page pilot scope
- documented input samples
- explicit success metrics

### Phase 2: Demo with believable workflow output

Use the current repo to demonstrate:

- workflow steps
- extracted fields
- routing target
- decision trace
- mocked Oracle handoff
- audit event ID

This is stronger than a generic AI chat demo because it looks like an
operations tool, not just a model response.

### Phase 3: Add customer-specific business rules

The fastest way to improve close probability is to encode one or two rules that
the customer immediately recognizes as theirs.

Examples:

- invoice approval thresholds by business unit
- required PO behavior by spend type
- payer-specific prior auth review rules
- diagnosis-to-procedure exceptions

### Phase 4: Swap mocks for guided integrations

Do not wait for production integration to start the pilot. Replace mocks in
layers:

- first: mocked Oracle handoff objects
- second: API contract adapters
- third: non-production environment integration
- fourth: production-hardening and monitoring

### Phase 5: Close with auditability and control

Customers buy faster when they can answer:

- who ran the automation
- what decision was made
- why the decision was made
- where the case was routed
- what system would receive it next

That is why audit IDs, decision traces, and integration artifacts matter even in
an early POC.

## Recommended pilot package

For each new customer, prepare:

- a customer-specific `.env` profile
- 3 to 5 realistic sample documents
- one finance demo flow and one exception flow
- one healthcare standard flow and one escalation flow
- a screenshot or live walkthrough of audit events
- a short integration roadmap showing mock-to-live progression

## Technical expansion paths

### Finance / Oracle ERP

- supplier master lookup
- purchase order and receipt matching
- invoice hold reasons
- AP import batch creation
- anomaly detection over historical invoice patterns

### Healthcare / Oracle Health

- eligibility and benefits lookup
- FHIR resource adapters
- authorization status tracking
- clinician review queues
- payer-specific medical necessity rules

### Shared platform

- authentication and RBAC
- case persistence
- document ingestion
- vector retrieval
- observability dashboards
- tenant isolation

## Delivery checklist

Before each customer meeting, verify:

- frontend loads on `5401`
- backend docs load on `5405/docs`
- both workflows run successfully
- audit events are created
- decision trace is visible
- mocked Oracle handoff artifacts are visible
- one customer-specific scenario is prepared
- next-step architecture is documented

## Commercial advice

The best next deal usually comes from showing a short path from:

- mocked but believable workflow
- to low-risk integration
- to measurable business value

Do not lead with platform abstraction. Lead with one costly workflow, one clear
decision path, and one credible integration plan.

## Reusable accelerators already available locally

The review of `/Users/josekurian/AIAgents` changes the practical delivery plan.
You already own far more reusable capability than this starter alone exposes.

### Best assets to reuse immediately

- `MCPPlatform` for approved MCP server overlays and shared runtime policy
- `MCPEngine` for audit, approvals, replay protection, and governance
- `EnterpriseAgents` for broader packaged agent and workflow definitions
- `OracleFinancialsFrontierFullImplementation` for finance-oriented agent teams,
  workflow specs, typed tool contracts, and scorecard patterns
- Oracle Health extension catalogs for expanding the current prior-auth POC into
  a more credible payer/provider operations package

### Customer POC packaging strategy

For a new customer POC, build the proposal around three layers:

1. the current `HybridAIAutomation` UI and lightweight API shell
2. imported workflow and agent patterns from the local Oracle finance or health
   catalogs
3. shared MCP and governance services from `MCPPlatform` and `MCPEngine`

That gives you a faster route to:

- domain credibility
- stronger auditability
- safer tool access
- a better production migration story

## Platform changes that improve POC sellability

### OpenAI implications as of 2026-04-29

- Remote MCP servers and connectors are now a documented first-class Responses
  API pattern, which makes your MCP-based reuse strategy commercially cleaner.
- The April 2026 OpenAI changelog introduces GPT-5.5 and GPT-5.5 pro in the
  Responses API, with support for MCP, tool search, web search, hosted shell,
  and structured outputs.
- Deep research models now support web search, remote MCP servers, and file
  search over vector stores, which opens a stronger analyst-assistant motion for
  customer discovery, audit investigation, and policy analysis.

### Oracle implications as of 2026-04-29

- Oracle expanded AI Agent Studio on March 24, 2026 with an Agentic
  Applications Builder plus workflow orchestration, contextual memory, content
  intelligence, and ROI measurement.
- Oracle introduced Fusion Agentic Applications for finance, supply chain, and
  HR on April 9, 2026. That matters because buyers are now hearing a stronger
  "agentic applications" message, not just isolated AI agents.
- OCI Enterprise AI reached GA on March 31, 2026 with an OpenAI-compatible
  Responses API, remote MCP calling, file search, vector stores, and containers,
  which improves the OCI-first deployment path for this repo.

## Expansion plays for new customer projects

### Finance

- AP invoice intake and duplicate detection
- payment hold resolution
- supplier exception handling
- invoice-to-payment status tracking
- close and controls evidence packs

### Healthcare

- prior authorization
- denial recovery
- referral closure
- patient intake to encounter
- revenue-cycle daily close

### Shared enterprise platform

- MCP-backed retrieval and action tools
- customer-specific approval policies
- trace scorecards and audit dashboards
- reusable agent team templates
- OCI vector search and enterprise knowledge retrieval
