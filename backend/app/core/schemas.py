from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentType = Literal["invoice", "prior_authorization"]
ProviderType = Literal["local", "openai", "oci"]
WorkflowName = Literal["invoice_processing", "prior_authorization"]


class RetrievedContext(BaseModel):
    source: str
    excerpt: str
    relevance: float = Field(ge=0.0, le=1.0)


class DecisionTraceItem(BaseModel):
    step: str
    detail: str


class IntegrationResult(BaseModel):
    system: str
    action: str
    status: Literal["prepared", "simulated", "completed", "failed", "not_applicable"]
    reference: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TeamMember(BaseModel):
    agent_id: str
    name: str
    role: str
    status: Literal["ready", "completed", "flagged", "skipped"]
    notes: list[str] = Field(default_factory=list)


class TeamHandoff(BaseModel):
    from_agent: str
    to_agent: str
    reason: str
    status: Literal["planned", "completed", "flagged", "skipped"]


class SpecialistFinding(BaseModel):
    agent_id: str
    title: str
    detail: str
    severity: Literal["info", "warning", "critical"] = "info"


class MultiAgentExecution(BaseModel):
    team_id: str
    team_name: str
    orchestration_mode: Literal["sequential", "supervisor", "parallel_review"]
    members: list[TeamMember] = Field(default_factory=list)
    handoffs: list[TeamHandoff] = Field(default_factory=list)
    findings: list[SpecialistFinding] = Field(default_factory=list)


class AgentRunRequest(BaseModel):
    agent_type: AgentType
    document_text: str = Field(
        min_length=20,
        description="Raw OCR output or copied text from a document.",
    )
    provider: ProviderType = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)
    use_retrieval: bool = True


class AgentRunResponse(BaseModel):
    agent_type: AgentType
    provider: ProviderType
    status: Literal["completed", "completed_with_fallback"]
    summary: str
    extracted_fields: dict[str, Any]
    next_actions: list[str]
    routing_target: str
    confidence: float = Field(ge=0.0, le=1.0)
    retrieved_context: list[RetrievedContext] = Field(default_factory=list)
    decision_trace: list[DecisionTraceItem] = Field(default_factory=list)
    integration_results: list[IntegrationResult] = Field(default_factory=list)
    processing_notes: list[str] = Field(default_factory=list)
    audit_event_id: str | None = None
    orchestration: MultiAgentExecution | None = None
    estimated_input_tokens: int | None = None
    estimated_output_tokens: int | None = None
    mcp_tool_calls: list["MCPToolCallResponse"] = Field(default_factory=list)


class WorkflowStepDefinition(BaseModel):
    id: str
    action: str
    agent: str | None = None
    target: str | None = None
    when: str | None = None


class WorkflowDefinition(BaseModel):
    name: WorkflowName
    version: int
    description: str
    mapped_agent_type: AgentType
    steps: list[WorkflowStepDefinition]


class WorkflowRunRequest(BaseModel):
    document_text: str = Field(
        min_length=20,
        description="Raw OCR output or copied text from a document.",
    )
    provider: ProviderType = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)
    use_retrieval: bool = True


class WorkflowStepResult(BaseModel):
    id: str
    action: str
    status: Literal["completed", "skipped", "flagged"]
    detail: str


class WorkflowRunResponse(BaseModel):
    workflow_name: WorkflowName
    workflow_version: int
    status: Literal["completed", "completed_with_flags"]
    steps: list[WorkflowStepResult]
    agent_result: AgentRunResponse


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    scopes: list[str] = Field(default_factory=list)


class ActorContext(BaseModel):
    subject: str
    role: str = "operator"
    auth_mode: Literal["anonymous", "token"] = "anonymous"
    scopes: list[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_id: str
    event_type: str
    actor: str
    occurred_at: datetime
    workflow_name: WorkflowName | None = None
    agent_type: AgentType
    provider: ProviderType
    status: str
    routing_target: str
    confidence: float = Field(ge=0.0, le=1.0)
    input_preview: str
    summary: str
    decision_trace: list[DecisionTraceItem] = Field(default_factory=list)
    integration_results: list[IntegrationResult] = Field(default_factory=list)


class TemplateFieldDefinition(BaseModel):
    name: str
    label: str
    required: bool = True
    example: str | None = None


class AgentTemplate(BaseModel):
    template_id: str
    name: str
    domain: Literal["finance", "healthcare"]
    mapped_agent_type: AgentType
    summary: str
    natural_language_prompt: str
    orchestration_mode: Literal["sequential", "supervisor", "parallel_review"]
    data_sources: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    sample_use_case_ids: list[str] = Field(default_factory=list)
    fields: list[TemplateFieldDefinition] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SampleUseCase(BaseModel):
    use_case_id: str
    title: str
    domain: Literal["finance", "healthcare"]
    template_id: str
    workflow_name: WorkflowName
    provider: ProviderType = "local"
    expected_route: str
    sample_document_text: str
    enabled_capabilities: list[str] = Field(default_factory=list)
    outcome_summary: str


class BuilderRequest(BaseModel):
    template_id: str
    workflow_name: str = Field(min_length=3)
    display_name: str = Field(min_length=3)
    provider: ProviderType = "local"
    enabled_tools: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    credential_aliases: list[str] = Field(default_factory=list)
    custom_instructions: str = ""
    thresholds: dict[str, float] = Field(default_factory=dict)


class BuilderNode(BaseModel):
    node_id: str
    title: str
    kind: Literal["intake", "retrieval", "specialist", "validation", "integration", "approval"]
    depends_on: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)


class BuilderResponse(BaseModel):
    blueprint_id: str
    template_id: str
    workflow_name: str
    display_name: str
    provider: ProviderType
    orchestration_mode: Literal["sequential", "supervisor", "parallel_review"]
    nodes: list[BuilderNode] = Field(default_factory=list)
    credential_aliases: list[str] = Field(default_factory=list)
    enabled_tools: list[str] = Field(default_factory=list)
    sample_payload: dict[str, Any] = Field(default_factory=dict)


class CredentialCreateRequest(BaseModel):
    alias: str = Field(min_length=3)
    secret_value: str = Field(min_length=6)
    scope: str = Field(min_length=3)
    integrations: list[str] = Field(default_factory=list)


class CredentialRecord(BaseModel):
    alias: str
    scope: str
    integrations: list[str] = Field(default_factory=list)
    masked_value: str
    created_at: datetime


class ValidationCheck(BaseModel):
    name: str
    status: Literal["passed", "warning", "failed"]
    detail: str


class ValidationScenarioResult(BaseModel):
    use_case_id: str
    workflow_name: WorkflowName
    status: Literal["passed", "warning", "failed"]
    expected_route: str
    actual_route: str
    summary: str


class ValidationReport(BaseModel):
    blueprint_id: str | None = None
    overall_status: Literal["passed", "warning", "failed"]
    checks: list[ValidationCheck] = Field(default_factory=list)
    scenario_results: list[ValidationScenarioResult] = Field(default_factory=list)


class MonitoringSnapshot(BaseModel):
    generated_at: datetime
    total_runs: int
    success_rate: float = Field(ge=0.0, le=1.0)
    average_latency_ms: float = Field(ge=0.0)
    error_rate: float = Field(ge=0.0, le=1.0)
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    runs_by_workflow: dict[str, int] = Field(default_factory=dict)
    runs_by_provider: dict[str, int] = Field(default_factory=dict)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


class RestIntegrationDefinition(BaseModel):
    integration_id: str
    name: str
    domain: Literal["finance", "healthcare", "shared"]
    method: Literal["GET", "POST", "PATCH"]
    path: str
    privilege_hint: str
    required_credential_scope: str
    sample_payload: dict[str, Any] = Field(default_factory=dict)
    mapped_use_case_ids: list[str] = Field(default_factory=list)


class RestSimulationRequest(BaseModel):
    integration_id: str
    credential_alias: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class RestSimulationResponse(BaseModel):
    integration_id: str
    status: Literal["prepared", "simulated", "failed"]
    reference: str
    endpoint: str
    request_preview: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class MarketplaceItem(BaseModel):
    item_id: str
    name: str
    publisher: str
    domain: Literal["finance", "healthcare", "shared"]
    summary: str
    capabilities: list[str] = Field(default_factory=list)
    template_id: str
    validated_for: list[str] = Field(default_factory=list)


class MarketplaceInstallResponse(BaseModel):
    item_id: str
    blueprint: BuilderResponse
    notes: list[str] = Field(default_factory=list)


class StudioOverview(BaseModel):
    templates: list[AgentTemplate] = Field(default_factory=list)
    sample_use_cases: list[SampleUseCase] = Field(default_factory=list)
    credentials: list[CredentialRecord] = Field(default_factory=list)
    monitoring: MonitoringSnapshot
    integrations: list[RestIntegrationDefinition] = Field(default_factory=list)
    marketplace_items: list[MarketplaceItem] = Field(default_factory=list)


class MCPToolContract(BaseModel):
    type: Literal["function"] = "function"
    server_label: str
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    require_approval: Literal["always", "never"] = "always"


class MCPServerContract(BaseModel):
    server_label: str
    server_description: str
    server_url: str
    require_approval: Literal["always", "never"] = "always"
    allowed_tools: list[str] = Field(default_factory=list)


class MCPToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    workflow_name: WorkflowName | None = None


class MCPToolCallResponse(BaseModel):
    tool: MCPToolContract
    status: Literal["completed", "failed"]
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    reference: str | None = None
    notes: list[str] = Field(default_factory=list)


class A2AAgentCard(BaseModel):
    card_id: str
    version: str
    agent_id: str
    name: str
    domain: Literal["finance", "healthcare", "shared"]
    summary: str
    role: str
    endpoint: str
    connector_type: Literal["rest", "mcp", "internal"]
    supported_scopes: list[str] = Field(default_factory=list)
    accepted_context_schema: dict[str, Any] = Field(default_factory=dict)
    produced_context_schema: dict[str, Any] = Field(default_factory=dict)
    handoff_targets: list[str] = Field(default_factory=list)
