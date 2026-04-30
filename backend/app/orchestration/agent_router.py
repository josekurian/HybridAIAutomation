from time import perf_counter

from ..agents.invoice_agent import InvoiceAgent
from ..agents.prior_auth_agent import PriorAuthAgent
from ..audit.service import AuditLogger
from ..ai.oci_ai_client import OCIAIClient
from ..ai.openai_client import OpenAIClient
from ..core.config import Settings
from ..core.schemas import ActorContext, AgentRunRequest, AgentRunResponse, WorkflowName
from ..integrations.oracle_erp import OracleERPClient
from ..integrations.oracle_health import OracleHealthClient
from ..protocols.mcp_runtime import MCPRuntime
from ..rag.retrieval import DomainRetriever
from ..studio.service import get_monitoring_service
from .team_orchestrator import TeamOrchestrator


class AgentRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.retriever = DomainRetriever()
        self.invoice_agent = InvoiceAgent()
        self.prior_auth_agent = PriorAuthAgent()
        self.openai_client = OpenAIClient(settings.openai_api_key, settings.openai_model)
        self.oci_client = OCIAIClient(
            settings.oci_ai_endpoint,
            settings.oci_ai_api_key,
            settings.oci_ai_model,
        )
        self.oracle_erp_client = OracleERPClient()
        self.oracle_health_client = OracleHealthClient()
        self.mcp_runtime = MCPRuntime()
        self.audit_logger = AuditLogger(settings)
        self.team_orchestrator = TeamOrchestrator()
        self.monitoring = get_monitoring_service()

    def route(self, task_type: str):
        if task_type == "invoice":
            return self.invoice_agent
        if task_type in {"prior_auth", "prior_authorization"}:
            return self.prior_auth_agent
        raise ValueError("Unknown agent")

    def run(
        self,
        request: AgentRunRequest,
        actor: ActorContext | None = None,
        workflow_name: WorkflowName | None = None,
    ) -> AgentRunResponse:
        started_at = perf_counter()
        actor = actor or ActorContext(subject="anonymous", auth_mode="anonymous")
        retrieved_context = (
            self.retriever.search(request.agent_type, request.document_text)
            if request.use_retrieval
            else []
        )

        if request.agent_type == "invoice":
            result = self.invoice_agent.analyze(request.document_text, retrieved_context)
        else:
            result = self.prior_auth_agent.analyze(request.document_text, retrieved_context)

        effective_provider = "local"
        notes: list[str] = []

        if request.provider == "openai":
            ai_summary, note = self._try_openai_summary(request, result)
            if ai_summary:
                result.summary = ai_summary
                effective_provider = "openai"
            if note:
                notes.append(note)
        elif request.provider == "oci":
            ai_summary, note = self._try_oci_summary(request, result)
            if ai_summary:
                result.summary = ai_summary
                effective_provider = "oci"
            if note:
                notes.append(note)

        result.provider = effective_provider
        result.processing_notes.extend(notes)
        if notes and effective_provider == "local" and request.provider != "local":
            result.status = "completed_with_fallback"

        if request.agent_type == "invoice":
            result.mcp_tool_calls = self._run_invoice_mcp_tools(result)
            result.integration_results = self.oracle_erp_client.build_invoice_actions(
                result,
                result.mcp_tool_calls,
            )
        else:
            result.mcp_tool_calls = self._run_prior_auth_mcp_tools(result)
            result.integration_results = self.oracle_health_client.build_prior_auth_actions(
                result,
                result.mcp_tool_calls,
            )

        result.orchestration = self.team_orchestrator.build_execution(result)
        result.estimated_input_tokens = self._estimate_tokens(request.document_text)
        result.estimated_output_tokens = self._estimate_tokens(
            " ".join(
                [
                    result.summary,
                    *result.next_actions,
                    *[item.detail for item in result.decision_trace],
                    *[item.detail for item in (result.orchestration.findings if result.orchestration else [])],
                ]
            )
        )
        result.audit_event_id = self.audit_logger.record_agent_run(
            actor=actor,
            request=request,
            response=result,
            workflow_name=workflow_name,
        )
        self.monitoring.record_run(
            workflow_name=workflow_name,
            agent_type=result.agent_type,
            provider=result.provider,
            latency_ms=(perf_counter() - started_at) * 1000,
            status=result.status,
            input_tokens=result.estimated_input_tokens or 0,
            output_tokens=result.estimated_output_tokens or 0,
            routing_target=result.routing_target,
        )

        return result

    def _try_openai_summary(
        self,
        request: AgentRunRequest,
        result: AgentRunResponse,
    ) -> tuple[str | None, str | None]:
        if not self.openai_client.is_configured():
            return None, "OPENAI_API_KEY is not set; returned the deterministic local summary."

        prompt = self._build_summary_prompt(request, result)
        try:
            summary = self.openai_client.summarize(
                instructions=(
                    "Summarize the workflow decision in at most two plain sentences. "
                    "Do not invent fields that are missing."
                ),
                prompt=prompt,
            )
            return summary, None
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            return None, f"OpenAI summary failed: {exc}"

    def _try_oci_summary(
        self,
        request: AgentRunRequest,
        result: AgentRunResponse,
    ) -> tuple[str | None, str | None]:
        if not self.oci_client.is_configured():
            return None, "OCI AI settings are incomplete; returned the deterministic local summary."

        prompt = self._build_summary_prompt(request, result)
        try:
            summary = self.oci_client.summarize(prompt)
            return summary, None
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            return None, f"OCI AI summary failed: {exc}"

    @staticmethod
    def _build_summary_prompt(request: AgentRunRequest, result: AgentRunResponse) -> str:
        return (
            f"Agent type: {request.agent_type}\n"
            f"Document text: {request.document_text}\n"
            f"Extracted fields: {result.extracted_fields}\n"
            f"Next actions: {result.next_actions}\n"
            f"Routing target: {result.routing_target}\n"
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, round(len(text) / 4))

    def _run_invoice_mcp_tools(self, result: AgentRunResponse):
        supplier_lookup = self.mcp_runtime.execute_tool(
            "oracle_erp_supplier_lookup",
            {
                "vendor": result.extracted_fields.get("vendor"),
                "supplier_number": result.extracted_fields.get("purchase_order_number"),
            },
        )
        invoice_import = self.mcp_runtime.execute_tool(
            "oracle_erp_ap_invoice_import",
            {
                "invoice_number": result.extracted_fields.get("invoice_number"),
                "amount_due": result.extracted_fields.get("amount_due"),
                "routing_target": result.routing_target,
                "purchase_order_number": result.extracted_fields.get("purchase_order_number"),
            },
        )
        return [supplier_lookup, invoice_import]

    def _run_prior_auth_mcp_tools(self, result: AgentRunResponse):
        eligibility = self.mcp_runtime.execute_tool(
            "oracle_health_eligibility_check",
            {
                "member_id": result.extracted_fields.get("member_id"),
                "payer": result.extracted_fields.get("payer"),
                "patient_name": result.extracted_fields.get("patient_name"),
            },
        )
        prior_auth_case = self.mcp_runtime.execute_tool(
            "oracle_health_prior_auth_case_create",
            {
                "member_id": result.extracted_fields.get("member_id"),
                "procedure": result.extracted_fields.get("procedure"),
                "diagnosis": result.extracted_fields.get("diagnosis"),
                "routing_target": result.routing_target,
            },
        )
        return [eligibility, prior_auth_case]
