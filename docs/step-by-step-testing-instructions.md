# Step-by-Step Testing Instructions

Version: `0.4.1`
Last updated: `2026-04-30`

This guide provides a repeatable step-by-step test plan for the current
`HybridAIAutomation` starter platform, including exact commands, what to verify,
and what responses to expect.

## Scope

The guide covers:

- service startup and health checks
- authentication and actor scope checks
- invoice and prior authorization agent runs
- workflow execution and audit events
- studio overview, blueprint composition, and validation
- credential creation and integration simulation
- marketplace install flow
- MCP and A2A protocol endpoints
- frontend manual smoke testing

## Assumptions

- the repo root is `/Users/josekurian/HybridAIAutomation`
- backend is exposed on `http://localhost:5405`
- frontend is exposed on `http://localhost:5401`
- demo credentials are:
  - username: `demo-admin`
  - password: `demo-password`

## Important Notes

- Dynamic values such as JWTs, timestamps, `audit_event_id`, `reference`, and
  `blueprint_id` will change on each run.
- Expected responses below show the fields and values that should be checked,
  not every byte of each payload.
- Commands use `python3` for JSON parsing so the test flow does not depend on
  `jq`.

## Test Setup

Run these once per shell session:

```bash
cd /Users/josekurian/HybridAIAutomation

export BASE_URL="http://localhost:5405"
export FRONTEND_URL="http://localhost:5401"
```

## 1. Start the Services

Start the backend and frontend:

```bash
docker compose up -d --no-deps backend frontend
```

Expected result:

- container `hybridaiautomation-backend-1` starts
- container `hybridaiautomation-frontend-1` starts
- backend listens on port `5405`
- frontend listens on port `5401`

Confirm with:

```bash
docker compose ps
```

Expected status:

- `backend` shows `Up`
- `frontend` shows `Up`

## 2. Verify Backend Health

Command:

```bash
curl -fsS "$BASE_URL/health"
```

Expected response:

```json
{"status":"ok","environment":"dev"}
```

Pass criteria:

- HTTP status `200`
- `status` is `ok`
- `environment` is `dev`

## 3. Issue a Demo Access Token

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/auth/token" \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo-admin","password":"demo-password"}'
```

Expected response excerpt:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "demo-admin",
  "scopes": ["agents:read", "agents:run", "workflows:read", "workflows:run"]
}
```

Pass criteria:

- HTTP status `200`
- `token_type` is `bearer`
- `access_token` is non-empty
- `role` is `demo-admin`
- `scopes` includes `protocols:mcp:execute`

Store the token for later steps:

```bash
export TOKEN=$(
  curl -fsS -X POST "$BASE_URL/api/v1/auth/token" \
    -H 'Content-Type: application/json' \
    -d '{"username":"demo-admin","password":"demo-password"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)
```

## 4. Verify Actor Identity

Command:

```bash
curl -fsS "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
{
  "subject": "demo-admin",
  "role": "demo-admin",
  "auth_mode": "token",
  "scopes": ["agents:read", "agents:run", "workflows:run"]
}
```

Pass criteria:

- HTTP status `200`
- `subject` is `demo-admin`
- `auth_mode` is `token`
- `scopes` includes `studio:build`

## 5. Verify Agent Catalog

Command:

```bash
curl -fsS "$BASE_URL/api/v1/agents/catalog" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:

```json
[
  {
    "agent_type": "invoice",
    "description": "Extract invoice data and recommend AP routing."
  },
  {
    "agent_type": "prior_authorization",
    "description": "Review healthcare prior auth requests and next actions."
  }
]
```

Pass criteria:

- HTTP status `200`
- two agent entries are returned
- `invoice` and `prior_authorization` are both present

## 6. Run the Invoice Agent

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/agents/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_type": "invoice",
    "provider": "local",
    "document_text": "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
  }'
```

Expected response excerpt:

```json
{
  "agent_type": "invoice",
  "provider": "local",
  "status": "completed",
  "routing_target": "finance.ap_high_value",
  "confidence": 0.93,
  "audit_event_id": "audit-<dynamic>",
  "estimated_input_tokens": 31,
  "orchestration": {
    "team_id": "team_finance_invoice_ops",
    "team_name": "Finance Invoice Operations Team"
  }
}
```

Expected fields to verify:

- `extracted_fields.invoice_number` = `INV-2026-041`
- `extracted_fields.vendor` = `Northwind Medical Supplies`
- `routing_target` = `finance.ap_high_value`
- `next_actions` contains finance approval guidance
- `integration_results[0].system` = `oracle_erp`
- `mcp_tool_calls[0].tool.type` = `function`
- `orchestration.team_id` = `team_finance_invoice_ops`

## 7. Run the Prior Authorization Agent

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/agents/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_type": "prior_authorization",
    "provider": "local",
    "document_text": "Patient: Elena Carter Member ID: MBR-55291 Payer: Evergreen Health Plan Diagnosis: Lumbar radiculopathy Procedure: MRI lumbar spine Ordering Provider: Dr. Ravi Patel"
  }'
```

Expected response excerpt:

```json
{
  "agent_type": "prior_authorization",
  "provider": "local",
  "status": "completed",
  "routing_target": "healthcare.medical_review",
  "confidence": 0.92,
  "audit_event_id": "audit-<dynamic>",
  "orchestration": {
    "team_id": "team_prior_auth_command",
    "team_name": "Prior Authorization Command Team"
  }
}
```

Expected fields to verify:

- `extracted_fields.member_id` = `MBR-55291`
- `extracted_fields.payer` = `Evergreen Health Plan`
- `routing_target` = `healthcare.medical_review`
- `decision_trace` is non-empty
- `integration_results[0].system` = `oracle_health`
- `mcp_tool_calls` contains exactly two tool calls

## 8. Run the Invoice Workflow

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/workflows/invoice_processing/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "local",
    "document_text": "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
  }'
```

Expected response excerpt:

```json
{
  "workflow_name": "invoice_processing",
  "workflow_version": 1,
  "status": "completed",
  "steps": [
    {"id": "ingest", "status": "completed"},
    {"id": "extract", "status": "completed"},
    {"id": "validate", "status": "completed"},
    {"id": "route", "status": "completed"},
    {"id": "approve_high_value", "status": "completed"}
  ],
  "agent_result": {
    "routing_target": "finance.ap_high_value"
  }
}
```

Pass criteria:

- HTTP status `200`
- `workflow_name` = `invoice_processing`
- `steps` is non-empty
- `agent_result.audit_event_id` is present

## 9. Verify Audit Events

Command:

```bash
curl -fsS "$BASE_URL/api/v1/audit/events?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "event_id": "audit-<dynamic>",
    "event_type": "agent_run",
    "agent_type": "invoice",
    "provider": "local",
    "status": "completed",
    "routing_target": "finance.ap_high_value"
  }
]
```

Pass criteria:

- HTTP status `200`
- response is a list
- most recent items include invoice or prior auth runs created in earlier steps
- each event includes `event_id`, `summary`, `decision_trace`, and `integration_results`

## 10. Verify Studio Overview

Command:

```bash
curl -fsS "$BASE_URL/api/v1/studio/overview" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
{
  "templates": [
    {
      "template_id": "invoice-oracle-ap-supervisor",
      "domain": "finance"
    }
  ],
  "sample_use_cases": [
    {
      "use_case_id": "invoice-high-value-escalation",
      "expected_route": "finance.ap_high_value"
    }
  ],
  "monitoring": {
    "total_runs": 3,
    "success_rate": 1.0
  },
  "integrations": [],
  "marketplace_items": []
}
```

Expected fields to verify:

- at least one template exists
- at least one sample use case exists
- `monitoring` is present
- `templates[0].template_id` is usable in the next step

Capture the first template ID:

```bash
export TEMPLATE_ID=$(
  curl -fsS "$BASE_URL/api/v1/studio/overview" \
    -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["templates"][0]["template_id"])'
)
```

## 11. Compose a Blueprint

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/studio/builders/compose" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"workflow_name\": \"invoice_processing\",
    \"display_name\": \"invoice-blueprint\",
    \"provider\": \"local\",
    \"enabled_tools\": [],
    \"data_sources\": [],
    \"credential_aliases\": [],
    \"custom_instructions\": \"Compose starter invoice blueprint\",
    \"thresholds\": {\"high_value_amount\": 10000}
  }"
```

Expected response excerpt:

```json
{
  "blueprint_id": "bp-<dynamic>",
  "template_id": "invoice-oracle-ap-supervisor",
  "workflow_name": "invoice_processing",
  "orchestration_mode": "supervisor",
  "nodes": [
    {"node_id": "intake", "kind": "intake"},
    {"node_id": "retrieval", "kind": "retrieval"},
    {"node_id": "specialist-team", "kind": "specialist"},
    {"node_id": "validation", "kind": "validation"},
    {"node_id": "integration", "kind": "integration"},
    {"node_id": "approval", "kind": "approval"}
  ]
}
```

Pass criteria:

- HTTP status `200`
- `nodes` is non-empty
- `nodes` contains `intake`, `retrieval`, `specialist-team`, `validation`, `integration`, and `approval`

## 12. Validate the Blueprint

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/studio/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"workflow_name\": \"invoice_processing\",
    \"display_name\": \"invoice-blueprint\",
    \"provider\": \"local\",
    \"enabled_tools\": [],
    \"data_sources\": [],
    \"credential_aliases\": [],
    \"custom_instructions\": \"Validate starter invoice blueprint\",
    \"thresholds\": {\"high_value_amount\": 10000}
  }"
```

Expected response excerpt:

```json
{
  "blueprint_id": "bp-<dynamic>",
  "overall_status": "warning",
  "checks": [
    {"name": "template_exists", "status": "passed"},
    {"name": "tool_selection", "status": "passed"},
    {"name": "credential_resolution", "status": "warning"},
    {"name": "runtime_validation", "status": "passed"}
  ],
  "scenario_results": [
    {
      "use_case_id": "invoice-high-value-escalation",
      "status": "passed",
      "expected_route": "finance.ap_high_value",
      "actual_route": "finance.ap_high_value"
    }
  ]
}
```

Pass criteria:

- HTTP status `200`
- `checks` is non-empty
- `scenario_results` is non-empty
- `overall_status` may be `warning` when no credentials are attached

## 13. Create a Demo Credential

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/studio/credentials" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "alias": "oracle-health-doc-test",
    "secret_value": "secret-demo-token",
    "scope": "oracle_health",
    "integrations": ["oracle-health-eligibility"]
  }'
```

Expected response excerpt:

```json
{
  "alias": "oracle-health-doc-test",
  "scope": "oracle_health",
  "integrations": ["oracle-health-eligibility"],
  "masked_value": "se*************en"
}
```

Pass criteria:

- HTTP status `200`
- alias matches
- scope is `oracle_health`
- `masked_value` is masked, not plaintext

## 14. List Integrations

Command:

```bash
curl -fsS "$BASE_URL/api/v1/studio/integrations" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "integration_id": "oracle-erp-supplier-lookup",
    "domain": "finance",
    "method": "GET"
  },
  {
    "integration_id": "oracle-health-eligibility",
    "domain": "healthcare",
    "method": "POST"
  }
]
```

Pass criteria:

- HTTP status `200`
- finance and healthcare integrations are both present
- each item includes `path`, `required_credential_scope`, and `mapped_use_case_ids`

## 15. Simulate an Integration

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/studio/integrations/simulate" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "integration_id": "oracle-health-eligibility",
    "credential_alias": "oracle-health-doc-test",
    "payload": {
      "memberId": "MBR-55291",
      "payer": "Evergreen Health Plan"
    }
  }'
```

Expected response excerpt:

```json
{
  "integration_id": "oracle-health-eligibility",
  "status": "simulated",
  "reference": "SIM-<dynamic>",
  "endpoint": "/healthcareApi/v1/eligibility/check",
  "request_preview": {
    "memberId": "MBR-55291",
    "payer": "Evergreen Health Plan"
  }
}
```

Pass criteria:

- HTTP status `200`
- `status` is `simulated`
- `notes` mentions demo vault resolution for the selected alias

If the alias scope is wrong, expected fallback behavior is:

```json
{
  "status": "failed",
  "notes": ["Credential scope mismatch for the selected integration."]
}
```

## 16. List Marketplace Items

Command:

```bash
curl -fsS "$BASE_URL/api/v1/studio/marketplace/items" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "item_id": "mkp-oracle-ap-accelerator",
    "name": "Oracle AP Accelerator Pack",
    "domain": "finance"
  },
  {
    "item_id": "mkp-prior-auth-accelerator",
    "name": "Prior Authorization Recovery Pack",
    "domain": "healthcare"
  }
]
```

Pass criteria:

- HTTP status `200`
- at least one marketplace item exists
- returned items include `template_id` and `capabilities`

Capture the first item ID:

```bash
export ITEM_ID=$(
  curl -fsS "$BASE_URL/api/v1/studio/marketplace/items" \
    -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["item_id"])'
)
```

## 17. Install a Marketplace Item

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/studio/marketplace/items/$ITEM_ID/install" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
{
  "item_id": "mkp-oracle-ap-accelerator",
  "blueprint": {
    "template_id": "invoice-oracle-ap-supervisor",
    "workflow_name": "finance-mkp-oracle-ap-accelerator",
    "display_name": "Oracle AP Accelerator Pack"
  },
  "notes": [
    "Oracle AP Accelerator Pack installed as a local blueprint."
  ]
}
```

Pass criteria:

- HTTP status `200`
- `blueprint.template_id` is present
- `notes` states the install is non-destructive

## 18. List MCP Servers

Command:

```bash
curl -fsS "$BASE_URL/api/v1/protocols/mcp/servers" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "server_label": "oracle_erp",
    "require_approval": "always",
    "allowed_tools": [
      "oracle_erp_supplier_lookup",
      "oracle_erp_ap_invoice_import"
    ]
  },
  {
    "server_label": "oracle_health",
    "require_approval": "always"
  }
]
```

Pass criteria:

- HTTP status `200`
- two MCP server groups are present
- each entry includes `allowed_tools`

## 19. List MCP Tools

Command:

```bash
curl -fsS "$BASE_URL/api/v1/protocols/mcp/tools" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "type": "function",
    "server_label": "oracle_erp",
    "name": "oracle_erp_supplier_lookup"
  },
  {
    "type": "function",
    "server_label": "oracle_health",
    "name": "oracle_health_eligibility_check"
  }
]
```

Pass criteria:

- HTTP status `200`
- every tool uses `type = function`
- Oracle ERP and Oracle Health tools are both present

## 20. Execute an MCP Tool Call

Command:

```bash
curl -fsS -X POST "$BASE_URL/api/v1/protocols/mcp/tools/oracle_erp_supplier_lookup/call" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "arguments": {
      "vendor_name": "Northwind Medical Supplies",
      "invoice_number": "INV-2026-041"
    }
  }'
```

Expected response excerpt:

```json
{
  "status": "completed",
  "reference": "SUP-<dynamic-or-unknown>",
  "tool": {
    "name": "oracle_erp_supplier_lookup",
    "type": "function"
  }
}
```

Pass criteria:

- HTTP status `200`
- `status` is `completed`
- `reference` is present
- response includes the echoed `arguments`

Note:

- the sample call above returns `SUP-UNKNOWN` because the direct tool call
  arguments use `vendor_name` and `invoice_number`, while the richer invoice
  agent path internally maps fields into the supplier lookup flow differently

## 21. List A2A Agent Cards

Command:

```bash
curl -fsS "$BASE_URL/api/v1/protocols/a2a/cards" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
[
  {
    "card_id": "invoice-intake-analyst",
    "agent_id": "invoice-intake-analyst",
    "connector_type": "internal"
  },
  {
    "card_id": "eligibility-review-agent",
    "agent_id": "eligibility-review-agent",
    "connector_type": "mcp"
  }
]
```

Pass criteria:

- HTTP status `200`
- multiple cards are returned
- each card includes `supported_scopes`, `accepted_context_schema`, and `handoff_targets`

## 22. Fetch A2A Card Detail

Command:

```bash
curl -fsS "$BASE_URL/api/v1/protocols/a2a/cards/invoice-intake-analyst" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response excerpt:

```json
{
  "card_id": "invoice-intake-analyst",
  "agent_id": "invoice-intake-analyst",
  "name": "Invoice Intake Analyst",
  "accepted_context_schema": {
    "required": ["document_text"]
  },
  "handoff_targets": [
    "policy-validation-agent",
    "duplicate-risk-agent"
  ]
}
```

Pass criteria:

- HTTP status `200`
- `agent_id` is non-empty
- `accepted_context_schema` is present
- `handoff_targets` matches the expected downstream agents

## 23. Frontend Manual Smoke Test

Open the frontend:

- [http://localhost:5401](http://localhost:5401)

Manual checks:

1. The page loads without a blank screen or browser error.
2. The app auto-bootstraps a demo token.
3. Invoice sample content is visible by default.
4. Running the invoice workflow shows:
   - summary text
   - extracted fields
   - routing target `finance.ap_high_value`
   - team orchestration details
   - MCP tool call details
5. Switching to prior authorization and running the workflow shows:
   - routing target `healthcare.medical_review`
   - Oracle Health integration artifacts
   - team name `Prior Authorization Command Team`
6. Studio sections show templates, monitoring, marketplace items, and validation output.

Expected UI behavior:

- requests complete without auth prompts
- no fatal API error banners are shown
- result cards render structured fields instead of raw JSON dumps

## 24. Negative Tests

### Invalid Credentials

Command:

```bash
curl -sS -X POST "$BASE_URL/api/v1/auth/token" \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo-admin","password":"wrong-password"}'
```

Expected result:

- HTTP status `401`
- response contains:

```json
{"detail":"Invalid demo credentials."}
```

### Missing Bearer Token

Command:

```bash
curl -sS "$BASE_URL/api/v1/agents/catalog"
```

Expected result:

- HTTP status `401` or `403`
- response indicates missing or invalid authentication

## 25. Regression Checklist

Treat the test run as passing only if all of the following are true:

- backend `/health` returns `200`
- token issue returns `200`
- invoice agent returns `finance.ap_high_value`
- prior auth agent returns `healthcare.medical_review`
- invoice workflow returns completed steps
- audit events list the newly created `audit_event_id`
- studio overview returns templates and monitoring
- blueprint compose and validate both succeed
- integration simulation returns `simulated` with a valid credential alias
- marketplace install returns a blueprint
- MCP server, tool, and tool-call endpoints all respond successfully
- A2A card list and card detail both respond successfully
- frontend renders workflow results end to end

## Related Documents

- [README](../README.md)
- [Documentation Index](./README.md)
- [Implementation and Testing Guide](./implementation-and-testing-guide.md)
- [Repository Structure Guide](./repository-structure.md)
- [Architecture Overview](./architecture.md)
