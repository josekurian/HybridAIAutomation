from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.config import get_settings
from ...core.schemas import ActorContext, WorkflowDefinition, WorkflowName, WorkflowRunRequest, WorkflowRunResponse
from ...core.security import require_scopes
from ...orchestration.agent_router import AgentRouter
from ...workflows.registry import WorkflowRegistry
from ...workflows.service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])
workflow_registry = WorkflowRegistry()
workflow_service = WorkflowService(AgentRouter(get_settings()), workflow_registry)


@router.get("", response_model=list[WorkflowDefinition])
def list_workflows(
    actor: Annotated[ActorContext, Depends(require_scopes("workflows:read"))],
) -> list[WorkflowDefinition]:
    _ = actor
    return workflow_registry.list_workflows()


@router.get("/{workflow_name}", response_model=WorkflowDefinition)
def get_workflow(
    workflow_name: WorkflowName,
    actor: Annotated[ActorContext, Depends(require_scopes("workflows:read"))],
) -> WorkflowDefinition:
    _ = actor
    return workflow_registry.get_workflow(workflow_name)


@router.post("/{workflow_name}/run", response_model=WorkflowRunResponse)
def run_workflow(
    workflow_name: WorkflowName,
    request: WorkflowRunRequest,
    actor: Annotated[ActorContext, Depends(require_scopes("workflows:run"))],
) -> WorkflowRunResponse:
    return workflow_service.run(workflow_name=workflow_name, request=request, actor=actor)
