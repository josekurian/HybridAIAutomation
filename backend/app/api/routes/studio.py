from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.schemas import (
    AgentTemplate,
    BuilderRequest,
    BuilderResponse,
    CredentialCreateRequest,
    CredentialRecord,
    MarketplaceInstallResponse,
    MarketplaceItem,
    MonitoringSnapshot,
    RestIntegrationDefinition,
    RestSimulationRequest,
    RestSimulationResponse,
    SampleUseCase,
    StudioOverview,
    ValidationReport,
)
from ...core.security import require_scopes
from ...orchestration.agent_router import AgentRouter
from ...studio.service import get_studio_service
from ...workflows.registry import WorkflowRegistry
from ...workflows.service import WorkflowService
from ...core.config import get_settings

router = APIRouter(prefix="/studio", tags=["studio"])
studio_service = get_studio_service()
workflow_service = WorkflowService(AgentRouter(get_settings()), WorkflowRegistry())


@router.get("/overview", response_model=StudioOverview)
def get_overview(
    actor: Annotated[object, Depends(require_scopes("studio:read"))],
) -> StudioOverview:
    _ = actor
    return studio_service.overview()


@router.get("/templates", response_model=list[AgentTemplate])
def list_templates(
    actor: Annotated[object, Depends(require_scopes("studio:read"))],
) -> list[AgentTemplate]:
    _ = actor
    return studio_service.list_templates()


@router.get("/use-cases", response_model=list[SampleUseCase])
def list_use_cases(
    actor: Annotated[object, Depends(require_scopes("studio:read"))],
) -> list[SampleUseCase]:
    _ = actor
    return studio_service.list_use_cases()


@router.post("/builders/compose", response_model=BuilderResponse)
def compose_blueprint(
    request: BuilderRequest,
    actor: Annotated[object, Depends(require_scopes("studio:build"))],
) -> BuilderResponse:
    _ = actor
    return studio_service.build_blueprint(request)


@router.post("/validate", response_model=ValidationReport)
def validate_blueprint(
    request: BuilderRequest,
    actor: Annotated[object, Depends(require_scopes("studio:validate"))],
) -> ValidationReport:
    _ = actor
    return studio_service.validate_blueprint(request, workflow_service)


@router.get("/credentials", response_model=list[CredentialRecord])
def list_credentials(
    actor: Annotated[object, Depends(require_scopes("studio:credentials:read"))],
) -> list[CredentialRecord]:
    _ = actor
    return studio_service.list_credentials()


@router.post("/credentials", response_model=CredentialRecord)
def create_credential(
    request: CredentialCreateRequest,
    actor: Annotated[object, Depends(require_scopes("studio:credentials:manage"))],
) -> CredentialRecord:
    _ = actor
    return studio_service.create_credential(request)


@router.get("/monitoring", response_model=MonitoringSnapshot)
def get_monitoring(
    actor: Annotated[object, Depends(require_scopes("studio:monitoring:read"))],
) -> MonitoringSnapshot:
    _ = actor
    return studio_service.monitoring_snapshot()


@router.get("/integrations", response_model=list[RestIntegrationDefinition])
def list_integrations(
    actor: Annotated[object, Depends(require_scopes("studio:integrations:read"))],
) -> list[RestIntegrationDefinition]:
    _ = actor
    return studio_service.list_integrations()


@router.post("/integrations/simulate", response_model=RestSimulationResponse)
def simulate_integration(
    request: RestSimulationRequest,
    actor: Annotated[object, Depends(require_scopes("studio:integrations:run"))],
) -> RestSimulationResponse:
    _ = actor
    return studio_service.simulate_integration(request)


@router.get("/marketplace/items", response_model=list[MarketplaceItem])
def list_marketplace_items(
    actor: Annotated[object, Depends(require_scopes("studio:marketplace:read"))],
) -> list[MarketplaceItem]:
    _ = actor
    return studio_service.list_marketplace_items()


@router.post("/marketplace/items/{item_id}/install", response_model=MarketplaceInstallResponse)
def install_marketplace_item(
    item_id: str,
    actor: Annotated[object, Depends(require_scopes("studio:marketplace:install"))],
) -> MarketplaceInstallResponse:
    _ = actor
    return studio_service.install_marketplace_item(item_id)
