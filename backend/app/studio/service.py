from __future__ import annotations

from functools import lru_cache
from time import perf_counter
from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi import HTTPException, status

from ..core.config import Settings, get_settings
from ..core.schemas import (
    ActorContext,
    BuilderNode,
    BuilderRequest,
    BuilderResponse,
    CredentialCreateRequest,
    CredentialRecord,
    MarketplaceInstallResponse,
    MonitoringSnapshot,
    RestIntegrationDefinition,
    RestSimulationRequest,
    RestSimulationResponse,
    StudioOverview,
    ValidationCheck,
    ValidationReport,
    ValidationScenarioResult,
    WorkflowRunRequest,
)
from .credentials import CredentialStore
from .monitoring import MonitoringService
from .registry import StudioRegistry

if TYPE_CHECKING:
    from ..workflows.service import WorkflowService


class StudioService:
    def __init__(
        self,
        settings: Settings,
        registry: StudioRegistry,
        credential_store: CredentialStore,
        monitoring: MonitoringService,
    ) -> None:
        self.settings = settings
        self.registry = registry
        self.credential_store = credential_store
        self.monitoring = monitoring

    def overview(self) -> StudioOverview:
        return StudioOverview(
            templates=self.registry.list_templates(),
            sample_use_cases=self.registry.list_use_cases(),
            credentials=self.credential_store.list_records(),
            monitoring=self.monitoring.snapshot(),
            integrations=self.registry.list_integrations(),
            marketplace_items=self.registry.list_marketplace_items(),
        )

    def list_templates(self):
        return self.registry.list_templates()

    def list_use_cases(self):
        return self.registry.list_use_cases()

    def list_credentials(self) -> list[CredentialRecord]:
        return self.credential_store.list_records()

    def create_credential(self, request: CredentialCreateRequest) -> CredentialRecord:
        return self.credential_store.create(request)

    def list_integrations(self) -> list[RestIntegrationDefinition]:
        return self.registry.list_integrations()

    def list_marketplace_items(self):
        return self.registry.list_marketplace_items()

    def build_blueprint(self, request: BuilderRequest) -> BuilderResponse:
        try:
            template = self.registry.get_template(request.template_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.") from exc

        blueprint_id = f"bp-{uuid4().hex[:10]}"
        nodes = [
            BuilderNode(
                node_id="intake",
                title="Intake and normalization",
                kind="intake",
                configuration={"mapped_agent_type": template.mapped_agent_type},
            ),
            BuilderNode(
                node_id="retrieval",
                title="Domain retrieval",
                kind="retrieval",
                depends_on=["intake"],
                configuration={"data_sources": request.data_sources or template.data_sources},
            ),
            BuilderNode(
                node_id="specialist-team",
                title="Specialist team orchestration",
                kind="specialist",
                depends_on=["retrieval"],
                configuration={
                    "mode": template.orchestration_mode,
                    "tools": request.enabled_tools or template.tools,
                },
            ),
            BuilderNode(
                node_id="validation",
                title="Validation and testing gate",
                kind="validation",
                depends_on=["specialist-team"],
                configuration={"thresholds": request.thresholds},
            ),
            BuilderNode(
                node_id="integration",
                title="REST API integration handoff",
                kind="integration",
                depends_on=["validation"],
                configuration={"credential_aliases": request.credential_aliases},
            ),
            BuilderNode(
                node_id="approval",
                title="Approval and publishing",
                kind="approval",
                depends_on=["integration"],
                configuration={"custom_instructions": request.custom_instructions.strip()},
            ),
        ]
        sample_use_case = None
        if template.sample_use_case_ids:
            sample_use_case = self.registry.get_use_case(template.sample_use_case_ids[0])

        return BuilderResponse(
            blueprint_id=blueprint_id,
            template_id=template.template_id,
            workflow_name=request.workflow_name,
            display_name=request.display_name,
            provider=request.provider,
            orchestration_mode=template.orchestration_mode,
            nodes=nodes,
            credential_aliases=request.credential_aliases,
            enabled_tools=request.enabled_tools or template.tools,
            sample_payload={
                "document_text": sample_use_case.sample_document_text if sample_use_case else "",
                "provider": request.provider,
                "mapped_agent_type": template.mapped_agent_type,
            },
        )

    def validate_blueprint(self, request: BuilderRequest, workflow_service: WorkflowService) -> ValidationReport:
        started_at = perf_counter()
        blueprint = self.build_blueprint(request)
        checks = [
            ValidationCheck(
                name="template_exists",
                status="passed",
                detail=f"Template {request.template_id} resolved successfully.",
            ),
            ValidationCheck(
                name="tool_selection",
                status="passed" if blueprint.enabled_tools else "warning",
                detail=(
                    f"{len(blueprint.enabled_tools)} tools selected for the blueprint."
                    if blueprint.enabled_tools
                    else "No explicit tools selected; template defaults will be used."
                ),
            ),
        ]

        if request.credential_aliases:
            alias_status = all(self.credential_store.resolve(alias) for alias in request.credential_aliases)
            checks.append(
                ValidationCheck(
                    name="credential_resolution",
                    status="passed" if alias_status else "warning",
                    detail=(
                        "All referenced credentials resolved."
                        if alias_status
                        else "One or more credential aliases could not be resolved in the demo vault."
                    ),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name="credential_resolution",
                    status="warning",
                    detail="No credential aliases were attached; REST integrations will remain simulated.",
                )
            )

        template = self.registry.get_template(request.template_id)
        scenario_results: list[ValidationScenarioResult] = []
        for use_case_id in template.sample_use_case_ids[:2]:
            use_case = self.registry.get_use_case(use_case_id)
            run_response = workflow_service.run(
                workflow_name=use_case.workflow_name,
                request=WorkflowRunRequest(
                    document_text=use_case.sample_document_text,
                    provider=request.provider,
                    metadata={"validation_mode": True, "blueprint_id": blueprint.blueprint_id},
                    use_retrieval=True,
                ),
                actor=ActorContext(subject="validator", role="qa", auth_mode="anonymous"),
            )
            matched = run_response.agent_result.routing_target == use_case.expected_route
            scenario_results.append(
                ValidationScenarioResult(
                    use_case_id=use_case.use_case_id,
                    workflow_name=use_case.workflow_name,
                    status="passed" if matched else "warning",
                    expected_route=use_case.expected_route,
                    actual_route=run_response.agent_result.routing_target,
                    summary=run_response.agent_result.summary,
                )
            )

        elapsed_ms = (perf_counter() - started_at) * 1000
        checks.append(
            ValidationCheck(
                name="runtime_validation",
                status="passed",
                detail=f"Validation scenarios executed in {elapsed_ms:.2f} ms.",
            )
        )
        overall_status = "passed"
        if any(check.status == "failed" for check in checks) or any(
            result.status == "failed" for result in scenario_results
        ):
            overall_status = "failed"
        elif any(check.status == "warning" for check in checks) or any(
            result.status == "warning" for result in scenario_results
        ):
            overall_status = "warning"

        return ValidationReport(
            blueprint_id=blueprint.blueprint_id,
            overall_status=overall_status,
            checks=checks,
            scenario_results=scenario_results,
        )

    def simulate_integration(self, request: RestSimulationRequest) -> RestSimulationResponse:
        try:
            integration = self.registry.get_integration(request.integration_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.") from exc

        notes = [
            f"Privilege hint: {integration.privilege_hint}.",
            "This is a simulated REST handoff for demo environments.",
        ]
        if request.credential_alias:
            if not self.credential_store.has_scope(request.credential_alias, integration.required_credential_scope):
                return RestSimulationResponse(
                    integration_id=integration.integration_id,
                    status="failed",
                    reference=f"SIM-{uuid4().hex[:8]}",
                    endpoint=integration.path,
                    request_preview=request.payload or integration.sample_payload,
                    notes=notes + ["Credential scope mismatch for the selected integration."],
                )
            notes.append(f"Credential alias {request.credential_alias} resolved through the demo vault.")
        else:
            notes.append("No credential alias supplied, so the request remained a dry-run simulation.")

        return RestSimulationResponse(
            integration_id=integration.integration_id,
            status="simulated",
            reference=f"SIM-{uuid4().hex[:8]}",
            endpoint=integration.path,
            request_preview=request.payload or integration.sample_payload,
            notes=notes,
        )

    def install_marketplace_item(self, item_id: str) -> MarketplaceInstallResponse:
        try:
            item = self.registry.get_marketplace_item(item_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace item not found.") from exc

        blueprint = self.build_blueprint(
            BuilderRequest(
                template_id=item.template_id,
                workflow_name=f"{item.domain}-{item.item_id}",
                display_name=item.name,
                provider="local",
                enabled_tools=item.capabilities,
                data_sources=["template_defaults"],
                credential_aliases=[],
                custom_instructions=f"Installed from marketplace item {item.name}.",
                thresholds={},
            )
        )
        return MarketplaceInstallResponse(
            item_id=item.item_id,
            blueprint=blueprint,
            notes=[
                f"{item.name} installed as a local blueprint.",
                "The install remains non-destructive and does not overwrite existing workflows.",
            ],
        )

    def monitoring_snapshot(self) -> MonitoringSnapshot:
        return self.monitoring.snapshot()


@lru_cache(maxsize=1)
def get_monitoring_service() -> MonitoringService:
    return MonitoringService()


@lru_cache(maxsize=1)
def get_studio_registry() -> StudioRegistry:
    return StudioRegistry()


@lru_cache(maxsize=1)
def get_credential_store() -> CredentialStore:
    return CredentialStore(get_settings().credential_store_path)


@lru_cache(maxsize=1)
def get_studio_service() -> StudioService:
    settings = get_settings()
    return StudioService(
        settings=settings,
        registry=get_studio_registry(),
        credential_store=get_credential_store(),
        monitoring=get_monitoring_service(),
    )
