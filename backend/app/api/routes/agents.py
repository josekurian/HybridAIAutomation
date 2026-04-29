from fastapi import APIRouter

from ...core.config import get_settings
from ...core.schemas import AgentRunRequest, AgentRunResponse
from ...orchestration.agent_router import AgentRouter

router = APIRouter(prefix="/agents", tags=["agents"])
agent_router = AgentRouter(get_settings())


@router.get("/catalog")
def get_catalog() -> list[dict[str, str]]:
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
def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    return agent_router.run(request)
