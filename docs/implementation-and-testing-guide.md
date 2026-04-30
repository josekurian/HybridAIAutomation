# HybridAIAutomation Implementation and Testing Guide

Version: `0.4.0`  
Last updated: `2026-04-29`

## 1. Purpose

This guide consolidates the current implementation state of the
`HybridAIAutomation` project and provides step-by-step testing instructions for
the two primary POC use cases:

- Invoice Processing
- Prior Authorization

It is intended to support local development, internal demos, customer POC
preparation, and technical review.

## 2. Project Scope

HybridAIAutomation is an enterprise-oriented AI automation starter platform
designed for Oracle ERP and healthcare workflows. The current version provides:

- a FastAPI backend with agent, workflow, auth, audit, studio, and protocol APIs
- a React frontend for running and reviewing workflow results
- mocked Oracle ERP and Oracle Health integration flows
- explainable decision traces and multi-agent orchestration output
- live MCP-style tool contracts and A2A agent-card contracts
- scoped authorization for protected APIs

## 3. Implemented Solution Areas

### 3.1 Backend Application

The backend is implemented under `backend/app` and is organized into layers.

Core implementation areas:

- `main.py`: FastAPI application bootstrap and route registration
- `api/routes`: REST endpoints for agents, workflows, auth, audit, studio, and protocols
- `agents`: domain-specific invoice and prior authorization logic
- `orchestration`: routing, team orchestration, and MCP-assisted execution
- `integrations`: Oracle ERP and Oracle Health simulation adapters
- `ai`: optional provider adapters for OpenAI and OCI AI
- `audit`: event logging and retrieval
- `core`: schemas, config, and authorization helpers
- `protocols`: MCP runtime and A2A agent-card registry
- `workflows`: workflow registry and execution service

### 3.2 Frontend Application

The frontend is implemented in `frontend/src/App.tsx` and provides:

- token bootstrap using the demo auth endpoint
- workflow selection and execution
- rendering of extracted fields, routing decisions, and next actions
- visibility into monitoring, marketplace, templates, and validation flows
- authenticated calls to protected backend endpoints

### 3.3 Deployment Assets

The repo includes local and cloud starter assets:

- `docker-compose.yml`: local backend, frontend, and database services
- `backend/Dockerfile`: backend image build
- `frontend/Dockerfile`: frontend image build
- `infrastructure/terraform/oci/main.tf`: OCI starter infrastructure
- `infrastructure/kubernetes/deployment.yaml`: Kubernetes starter deployment

## 4. Step-by-Step Implementation Details

### Step 1. Environment and Project Bootstrap

The project begins with a standard local development setup.

Implementation details:

- create `.env` from `.env.example`
- install backend dependencies from `backend/requirements.txt`
- install frontend dependencies with `npm install`
- run local services either individually or with Docker Compose

Expected outcome:

- frontend available at `http://localhost:5401`
- backend available at `http://localhost:5405`
- backend docs available at `http://localhost:5405/docs`

### Step 2. Core API and Schema Layer

The FastAPI service exposes a versioned API under `/api/v1`.

Implemented API groups:

- `/agents`
- `/workflows`
- `/auth`
- `/audit`
- `/studio`
- `/protocols`

Schema coverage includes:

- typed workflow requests and responses
- token and actor identity payloads
- audit event models
- MCP server, tool, and tool-call contracts
- A2A agent-card models

### Step 3. Domain Agents

Two domain agents are implemented:

#### Invoice Agent

Responsibilities:

- parse invoice number, vendor, amount due, due date, and PO number
- assess invoice completeness
- route to `finance.ap_standard` or `finance.ap_high_value`
- generate next actions and decision trace entries

#### Prior Authorization Agent

Responsibilities:

- parse patient name, member ID, payer, diagnosis, procedure, and ordering provider
- assess authorization completeness
- route to `healthcare.utilization_review` or `healthcare.medical_review`
- generate next actions and decision trace entries

### Step 4. Workflow Layer

The workflow layer binds business flow definitions to agent execution.

Implemented workflows:

- `invoice_processing`
- `prior_authorization`

Workflow execution returns:

- workflow name and version
- step-by-step workflow results
- the underlying agent result
- audit event identifiers

### Step 5. Multi-Agent Orchestration

The orchestration layer produces structured multi-agent output for both POCs.

Invoice orchestration includes:

- intake analyst
- policy validation agent
- duplicate risk agent
- Oracle AP handoff agent

Prior authorization orchestration includes:

- intake navigator agent
- eligibility review agent
- medical necessity agent
- Oracle Health handoff agent

Each run includes:

- team metadata
- participating members
- handoffs between agents
- specialist findings

### Step 6. MCP Protocol Implementation

Live MCP-style tool wiring has been implemented in the repo.

Implemented components:

- local MCP runtime
- MCP server registry
- tool contracts using OpenAI Responses API-style function shapes
- callable protocol endpoints for listing and executing tools

Current MCP server groups:

- `oracle_erp`
- `oracle_health`

Current MCP tools:

- `oracle_erp_supplier_lookup`
- `oracle_erp_ap_invoice_import`
- `oracle_health_eligibility_check`
- `oracle_health_prior_auth_case_create`

Runtime behavior:

- invoice flows call Oracle ERP-style tools during execution
- prior-auth flows call Oracle Health-style tools during execution
- tool calls are returned in `mcp_tool_calls` in the response payload

### Step 7. A2A Agent-Card Implementation

Externalized A2A contracts are implemented as JSON agent cards under:

- `backend/app/protocols/agent_cards`

Current cards cover:

- invoice intake analyst
- policy validation agent
- eligibility review agent
- Oracle Health handoff agent

Each card includes:

- card version
- agent identity
- domain
- endpoint
- connector type
- supported scopes
- accepted context schema
- produced context schema
- handoff targets

### Step 8. Security and Scoped Authorization

Protected APIs now require bearer tokens and explicit scopes.

Implemented security elements:

- JWT token issuance
- decoded actor context
- role-to-scope mapping
- per-route scope enforcement

Current roles:

- `demo-admin`
- `operator`
- `auditor`

Examples of enforced scopes:

- `agents:run`
- `workflows:run`
- `studio:build`
- `studio:validate`
- `studio:credentials:manage`
- `protocols:mcp:execute`
- `audit:read`

### Step 9. Audit and Monitoring

Every workflow and agent run can generate audit events.

Audit support includes:

- event IDs on responses
- event listing APIs
- confidence, summary, and routing capture
- integration result capture
- actor identity capture

Monitoring support includes:

- recent runs
- success rate
- error rate
- average latency
- estimated token totals

### Step 10. Frontend Experience

The frontend supports demo-grade operations for customer POCs.

Implemented interactions:

- bootstrap a token
- fetch platform overview
- run invoice workflow
- run prior-auth workflow
- compose low-code blueprints
- validate blueprints
- simulate integrations
- install marketplace packs

## 5. POC Use Cases

### 5.1 Invoice Processing POC

Business objective:

- accept invoice content
- extract operational fields
- assess completeness and amount threshold
- route standard vs high-value AP processing
- simulate Oracle ERP handoff

Sample scenario:

- Invoice Number: `INV-2026-041`
- Vendor: `Northwind Medical Supplies`
- Amount Due: `12480.00`
- Due Date: `2026-05-15`
- PO Number: `PO-88412`

Expected result:

- route to `finance.ap_high_value`
- return extraction data
- include MCP calls to ERP tools
- attach Oracle ERP integration results

### 5.2 Prior Authorization POC

Business objective:

- accept prior-auth request content
- extract member and clinical fields
- detect higher-acuity services
- route to standard or medical review
- simulate Oracle Health handoff

Sample scenario:

- Patient: `Elena Carter`
- Member ID: `MBR-55291`
- Payer: `Evergreen Health Plan`
- Diagnosis: `Lumbar radiculopathy`
- Procedure: `MRI lumbar spine`
- Ordering Provider: `Dr. Ravi Patel`

Expected result:

- route to `healthcare.medical_review`
- return extraction data
- include MCP calls to Oracle Health tools
- attach Oracle Health integration results

## 6. REST API Surface for Testing

Core endpoints:

- `GET /health`
- `POST /api/v1/auth/token`
- `POST /api/v1/agents/run`
- `POST /api/v1/workflows/invoice_processing/run`
- `POST /api/v1/workflows/prior_authorization/run`
- `GET /api/v1/audit/events`
- `GET /api/v1/studio/overview`
- `POST /api/v1/studio/builders/compose`
- `POST /api/v1/studio/validate`
- `GET /api/v1/protocols/mcp/servers`
- `GET /api/v1/protocols/mcp/tools`
- `POST /api/v1/protocols/mcp/tools/{tool_name}/call`
- `GET /api/v1/protocols/a2a/cards`

## 7. Step-by-Step Testing Guide

### Phase A. Local Startup Validation

1. Copy environment settings:

   ```bash
   cp .env.example .env
   ```

2. Start the stack:

   ```bash
   docker-compose up --build
   ```

3. Confirm backend health:

   ```bash
   curl http://localhost:5405/health
   ```

4. Open:

   - frontend: `http://localhost:5401`
   - backend docs: `http://localhost:5405/docs`

Expected result:

- backend returns `{"status":"ok"}`
- frontend loads without auth errors

### Phase B. Authentication Validation

1. Request a demo token:

   ```bash
   curl -X POST http://localhost:5405/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username":"demo-admin","password":"demo-password"}'
   ```

2. Confirm the response includes:

- `access_token`
- `token_type`
- `role`
- `scopes`

Expected result:

- role is `demo-admin`
- scopes include `protocols:mcp:execute`

### Phase C. Invoice POC API Test

1. Acquire a token and export it as `TOKEN`.
2. Run the invoice workflow:

   ```bash
   curl -X POST http://localhost:5405/api/v1/workflows/invoice_processing/run \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "local",
       "document_text": "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
     }'
   ```

3. Validate these fields in the response:

- `workflow_name`
- `steps`
- `agent_result.routing_target`
- `agent_result.extracted_fields`
- `agent_result.integration_results`
- `agent_result.mcp_tool_calls`
- `agent_result.audit_event_id`

Expected result:

- route target is `finance.ap_high_value`
- extracted invoice number is `INV-2026-041`
- at least one MCP tool call is returned

### Phase D. Prior Authorization POC API Test

1. Run the prior-auth workflow:

   ```bash
   curl -X POST http://localhost:5405/api/v1/workflows/prior_authorization/run \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "local",
       "document_text": "Patient: Elena Carter Member ID: MBR-55291 Payer: Evergreen Health Plan Diagnosis: Lumbar radiculopathy Procedure: MRI lumbar spine Ordering Provider: Dr. Ravi Patel"
     }'
   ```

2. Validate these fields in the response:

- `agent_result.routing_target`
- `agent_result.extracted_fields.member_id`
- `agent_result.decision_trace`
- `agent_result.mcp_tool_calls`

Expected result:

- route target is `healthcare.medical_review`
- member ID is `MBR-55291`
- two MCP tool calls are returned

### Phase E. MCP Protocol Validation

1. List servers:

   ```bash
   curl http://localhost:5405/api/v1/protocols/mcp/servers \
     -H "Authorization: Bearer $TOKEN"
   ```

2. List tools:

   ```bash
   curl http://localhost:5405/api/v1/protocols/mcp/tools \
     -H "Authorization: Bearer $TOKEN"
   ```

3. Execute an ERP tool:

   ```bash
   curl -X POST http://localhost:5405/api/v1/protocols/mcp/tools/oracle_erp_supplier_lookup/call \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "arguments": {
         "vendor_name": "Northwind Medical Supplies",
         "invoice_number": "INV-2026-041"
       }
     }'
   ```

Expected result:

- servers are returned with `allowed_tools`
- tools are returned with `type: function`
- tool call returns `status: completed`

### Phase F. A2A Agent-Card Validation

1. List A2A cards:

   ```bash
   curl http://localhost:5405/api/v1/protocols/a2a/cards \
     -H "Authorization: Bearer $TOKEN"
   ```

2. Retrieve an individual card:

   ```bash
   curl http://localhost:5405/api/v1/protocols/a2a/cards/invoice-intake-analyst \
     -H "Authorization: Bearer $TOKEN"
   ```

Expected result:

- at least one card is returned
- returned card includes schema and handoff metadata

### Phase G. Studio and Builder Validation

1. Request studio overview:

   ```bash
   curl http://localhost:5405/api/v1/studio/overview \
     -H "Authorization: Bearer $TOKEN"
   ```

2. Compose a workflow blueprint:

   ```bash
   curl -X POST http://localhost:5405/api/v1/studio/builders/compose \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "template_id": "invoice-oracle-ap-supervisor",
       "workflow_name": "invoice_processing",
       "display_name": "invoice-blueprint",
       "provider": "local",
       "enabled_tools": [],
       "data_sources": [],
       "credential_aliases": [],
       "custom_instructions": "Compose starter invoice blueprint",
       "thresholds": {"high_value_amount": 10000}
     }'
   ```

3. Validate the blueprint:

   ```bash
   curl -X POST http://localhost:5405/api/v1/studio/validate \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "template_id": "invoice-oracle-ap-supervisor",
       "workflow_name": "invoice_processing",
       "display_name": "invoice-blueprint",
       "provider": "local",
       "enabled_tools": [],
       "data_sources": [],
       "credential_aliases": [],
       "custom_instructions": "Validate starter invoice blueprint",
       "thresholds": {"high_value_amount": 10000}
     }'
   ```

Expected result:

- overview includes templates and monitoring
- blueprint includes nodes
- validation includes checks and scenario results

### Phase H. Automated Test Execution

Run the API test suite:

```bash
python3 -m pytest tests/test_api.py
```

Covered checks:

- health endpoint
- demo token issue
- invoice agent execution
- prior-auth agent execution
- workflow execution plus audit listing
- studio overview, compose, and validation
- credential, integration, and marketplace flows
- MCP and A2A protocol endpoints

Expected result:

- `8 passed`

### Phase I. Frontend Build Validation

Run the frontend build:

```bash
cd frontend
npm run build
```

Expected result:

- build succeeds
- generated static assets are written under `frontend/dist`

## 8. Current Known Limitations

- OCR ingestion is not yet implemented
- Oracle ERP and Oracle Health integrations are simulated, not live
- vector-backed retrieval is not yet wired
- document rendering QA for DOCX requires LibreOffice or `soffice`
- current auth is a strong demo baseline, not a full enterprise RBAC system

## 9. Recommended Next Expansion Steps

1. Replace simulated Oracle integrations with tenancy-specific adapters.
2. Integrate shared MCP overlays from `/Users/josekurian/AIAgents`.
3. Add persistence for cases, approvals, and audit history.
4. Introduce vector-backed retrieval and knowledge administration.
5. Add full RBAC, approval workflows, and hardened secret management.
6. Add regression packs for customer-specific invoice and prior-auth variants.

## 10. Implementation Status Summary

The current project is ready for:

- internal technical demonstration
- guided customer POC walkthroughs
- API-based workflow validation
- iterative expansion toward Oracle-connected enterprise pilots

The current project is not yet positioned as a production deployment without
further work in live integrations, persistence, compliance controls, and cloud
operational hardening.
