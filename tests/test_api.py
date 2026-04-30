from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def issue_demo_token() -> str:
    response = client.post(
        "/api/v1/auth/token",
        json={
            "username": "demo-admin",
            "password": "demo-password",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_demo_token()}"}


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invoice_agent_run() -> None:
    response = client.post(
        "/api/v1/agents/run",
        headers=auth_headers(),
        json={
            "agent_type": "invoice",
            "provider": "local",
            "document_text": (
                "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies "
                "Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
            ),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["agent_type"] == "invoice"
    assert payload["routing_target"] == "finance.ap_high_value"
    assert payload["extracted_fields"]["invoice_number"] == "INV-2026-041"
    assert payload["audit_event_id"]
    assert payload["integration_results"][0]["system"] == "oracle_erp"
    assert payload["orchestration"]["team_id"] == "team_finance_invoice_ops"
    assert payload["estimated_input_tokens"] > 0
    assert payload["mcp_tool_calls"]
    assert payload["mcp_tool_calls"][0]["tool"]["type"] == "function"


def test_prior_auth_agent_run() -> None:
    response = client.post(
        "/api/v1/agents/run",
        headers=auth_headers(),
        json={
            "agent_type": "prior_authorization",
            "provider": "local",
            "document_text": (
                "Patient: Elena Carter Member ID: MBR-55291 Payer: Evergreen Health Plan "
                "Diagnosis: Lumbar radiculopathy Procedure: MRI lumbar spine "
                "Ordering Provider: Dr. Ravi Patel"
            ),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["agent_type"] == "prior_authorization"
    assert payload["routing_target"] == "healthcare.medical_review"
    assert payload["extracted_fields"]["member_id"] == "MBR-55291"
    assert payload["decision_trace"]
    assert payload["integration_results"][0]["system"] == "oracle_health"
    assert payload["orchestration"]["team_name"] == "Prior Authorization Command Team"
    assert len(payload["mcp_tool_calls"]) == 2


def test_workflow_run_and_audit_listing() -> None:
    headers = auth_headers()
    response = client.post(
        "/api/v1/workflows/invoice_processing/run",
        headers=headers,
        json={
            "provider": "local",
            "document_text": (
                "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies "
                "Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
            ),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["workflow_name"] == "invoice_processing"
    assert payload["steps"]
    assert payload["agent_result"]["audit_event_id"]

    audit_response = client.get("/api/v1/audit/events?limit=5", headers=headers)
    audit_payload = audit_response.json()

    assert audit_response.status_code == 200
    assert any(
        event["event_id"] == payload["agent_result"]["audit_event_id"]
        for event in audit_payload
    )


def test_issue_demo_token() -> None:
    response = client.post(
        "/api/v1/auth/token",
        json={
            "username": "demo-admin",
            "password": "demo-password",
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["role"] == "demo-admin"
    assert "protocols:mcp:execute" in payload["scopes"]


def test_studio_overview_and_builder_validation() -> None:
    headers = auth_headers()
    overview_response = client.get("/api/v1/studio/overview", headers=headers)
    overview_payload = overview_response.json()

    assert overview_response.status_code == 200
    assert overview_payload["templates"]
    assert overview_payload["sample_use_cases"]
    assert "monitoring" in overview_payload

    template_id = overview_payload["templates"][0]["template_id"]
    compose_response = client.post(
        "/api/v1/studio/builders/compose",
        headers=headers,
        json={
            "template_id": template_id,
            "workflow_name": "invoice_processing",
            "display_name": "invoice-blueprint",
            "provider": "local",
            "enabled_tools": [],
            "data_sources": [],
            "credential_aliases": [],
            "custom_instructions": "Compose starter invoice blueprint",
            "thresholds": {"high_value_amount": 10000},
        },
    )
    compose_payload = compose_response.json()

    assert compose_response.status_code == 200
    assert compose_payload["nodes"]

    validate_response = client.post(
        "/api/v1/studio/validate",
        headers=headers,
        json={
            "template_id": template_id,
            "workflow_name": "invoice_processing",
            "display_name": "invoice-blueprint",
            "provider": "local",
            "enabled_tools": [],
            "data_sources": [],
            "credential_aliases": [],
            "custom_instructions": "Validate starter invoice blueprint",
            "thresholds": {"high_value_amount": 10000},
        },
    )
    validate_payload = validate_response.json()

    assert validate_response.status_code == 200
    assert validate_payload["checks"]
    assert validate_payload["scenario_results"]


def test_studio_credentials_integrations_and_marketplace() -> None:
    headers = auth_headers()
    credential_response = client.post(
        "/api/v1/studio/credentials",
        headers=headers,
        json={
            "alias": "oracle-health-demo",
            "secret_value": "secret-demo-token",
            "scope": "oracle_health",
            "integrations": ["oracle-health-eligibility"],
        },
    )
    credential_payload = credential_response.json()

    assert credential_response.status_code == 200
    assert credential_payload["alias"] == "oracle-health-demo"

    integrations_response = client.get("/api/v1/studio/integrations", headers=headers)
    integrations_payload = integrations_response.json()

    assert integrations_response.status_code == 200
    assert integrations_payload

    simulation_response = client.post(
        "/api/v1/studio/integrations/simulate",
        headers=headers,
        json={
            "integration_id": "oracle-health-eligibility",
            "credential_alias": "oracle-health-demo",
            "payload": {"memberId": "MBR-55291", "payer": "Evergreen Health Plan"},
        },
    )
    simulation_payload = simulation_response.json()

    assert simulation_response.status_code == 200
    assert simulation_payload["status"] == "simulated"

    marketplace_response = client.get(
        "/api/v1/studio/marketplace/items",
        headers=headers,
    )
    marketplace_payload = marketplace_response.json()

    assert marketplace_response.status_code == 200
    assert marketplace_payload

    install_response = client.post(
        f"/api/v1/studio/marketplace/items/{marketplace_payload[0]['item_id']}/install",
        headers=headers,
    )
    install_payload = install_response.json()

    assert install_response.status_code == 200
    assert install_payload["blueprint"]["template_id"]


def test_mcp_and_a2a_protocol_endpoints() -> None:
    headers = auth_headers()

    servers_response = client.get("/api/v1/protocols/mcp/servers", headers=headers)
    servers_payload = servers_response.json()

    assert servers_response.status_code == 200
    assert servers_payload
    assert "allowed_tools" in servers_payload[0]

    tools_response = client.get("/api/v1/protocols/mcp/tools", headers=headers)
    tools_payload = tools_response.json()

    assert tools_response.status_code == 200
    assert tools_payload
    assert tools_payload[0]["type"] == "function"

    tool_call_response = client.post(
        "/api/v1/protocols/mcp/tools/oracle_erp_supplier_lookup/call",
        headers=headers,
        json={
            "arguments": {
                "vendor_name": "Northwind Medical Supplies",
                "invoice_number": "INV-2026-041",
            }
        },
    )
    tool_call_payload = tool_call_response.json()

    assert tool_call_response.status_code == 200
    assert tool_call_payload["status"] == "completed"
    assert tool_call_payload["reference"]

    cards_response = client.get("/api/v1/protocols/a2a/cards", headers=headers)
    cards_payload = cards_response.json()

    assert cards_response.status_code == 200
    assert cards_payload

    card_id = cards_payload[0]["card_id"]
    card_response = client.get(f"/api/v1/protocols/a2a/cards/{card_id}", headers=headers)
    card_payload = card_response.json()

    assert card_response.status_code == 200
    assert card_payload["agent_id"]
    assert card_payload["accepted_context_schema"]
