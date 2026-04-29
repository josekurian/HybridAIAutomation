from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invoice_agent_run() -> None:
    response = client.post(
        "/api/v1/agents/run",
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


def test_prior_auth_agent_run() -> None:
    response = client.post(
        "/api/v1/agents/run",
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
