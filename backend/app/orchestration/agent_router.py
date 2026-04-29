from ..agents.invoice_agent import InvoiceAgent
from ..agents.prior_auth_agent import PriorAuthAgent
from ..ai.oci_ai_client import OCIAIClient
from ..ai.openai_client import OpenAIClient
from ..core.config import Settings
from ..core.schemas import AgentRunRequest, AgentRunResponse
from ..rag.retrieval import DomainRetriever


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

    def run(self, request: AgentRunRequest) -> AgentRunResponse:
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
