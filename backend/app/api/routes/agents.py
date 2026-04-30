from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from ...core.config import get_settings
from ...core.schemas import ActorContext, AgentRunRequest, AgentRunResponse
from ...core.security import require_scopes
from ...orchestration.agent_router import AgentRouter

router = APIRouter(prefix="/agents", tags=["agents"])
agent_router = AgentRouter(get_settings())


@router.get("/catalog")
def get_catalog(
    actor: Annotated[ActorContext, Depends(require_scopes("agents:read"))],
) -> list[dict[str, str]]:
    _ = actor
    return [
        {
            "agent_type": "invoice",
            "description": "Extract invoice data and recommend AP routing.",
        },
        {
            "agent_type": "prior_authorization",
            "description": "Review healthcare prior auth requests and next actions.",
        },
    ]


@router.post("/run", response_model=AgentRunResponse)
def run_agent(
    request: AgentRunRequest,
    actor: Annotated[ActorContext, Depends(require_scopes("agents:run"))],
) -> AgentRunResponse:
    return agent_router.run(request=request, actor=actor)


@router.post("/{task_type}", response_model=AgentRunResponse)
def run_task_type_agent(
    task_type: str,
    payload: Annotated[dict[str, Any], Body(...)],
    actor: Annotated[ActorContext, Depends(require_scopes("agents:run"))],
) -> AgentRunResponse:
    if task_type == "invoice":
        document_text = str(payload.get("document_text") or "").strip()
        if not document_text:
            file_path = str(payload.get("file_path") or "sample.pdf")
            document_text = (
                f"Invoice Number: DEMO-{file_path.upper().replace('.', '-')[:12]} "
                "Vendor: ABC Corp Amount Due: 1200.00 Due Date: 2026-06-15 PO Number: PO-DEMO-1001"
            )
        request = AgentRunRequest(
            agent_type="invoice",
            document_text=document_text,
            provider=str(payload.get("provider") or "local"),
            metadata=payload.get("metadata") or {},
            use_retrieval=bool(payload.get("use_retrieval", True)),
        )
    elif task_type in {"prior_auth", "prior_authorization"}:
        document_text = str(payload.get("document_text") or payload.get("clinical_note") or "").strip()
        if not document_text:
            document_text = (
                "Patient: Demo Patient Member ID: DEMO-4451 Payer: Evergreen Health Plan "
                "Diagnosis: Knee pain Procedure: MRI knee Ordering Provider: Dr. Demo"
            )
        request = AgentRunRequest(
            agent_type="prior_authorization",
            document_text=document_text,
            provider=str(payload.get("provider") or "local"),
            metadata=payload.get("metadata") or {},
            use_retrieval=bool(payload.get("use_retrieval", True)),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown agent type.",
        )
    return agent_router.run(request=request, actor=actor)
