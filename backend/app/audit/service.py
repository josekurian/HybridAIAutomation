import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..core.config import Settings
from ..core.schemas import ActorContext, AgentRunRequest, AgentRunResponse, AuditEvent, WorkflowName


class AuditLogger:
    def __init__(self, settings: Settings) -> None:
        self._path = Path(settings.audit_log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record_agent_run(
        self,
        actor: ActorContext,
        request: AgentRunRequest,
        response: AgentRunResponse,
        workflow_name: WorkflowName | None = None,
    ) -> str:
        event = AuditEvent(
            event_id=f"audit-{uuid4().hex[:12]}",
            event_type="agent_run",
            actor=actor.subject,
            occurred_at=datetime.now(UTC),
            workflow_name=workflow_name,
            agent_type=request.agent_type,
            provider=response.provider,
            status=response.status,
            routing_target=response.routing_target,
            confidence=response.confidence,
            input_preview=self._preview(request.document_text),
            summary=response.summary,
            decision_trace=response.decision_trace,
            integration_results=response.integration_results,
        )
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json())
            handle.write("\n")
        return event.event_id

    def list_events(self, limit: int = 20) -> list[AuditEvent]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
        events = [AuditEvent.model_validate(json.loads(line)) for line in lines]
        return list(reversed(events[-limit:]))

    def get_event(self, event_id: str) -> AuditEvent | None:
        if not self._path.exists():
            return None
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if payload.get("event_id") == event_id:
                    return AuditEvent.model_validate(payload)
        return None

    @staticmethod
    def _preview(document_text: str) -> str:
        compact = " ".join(document_text.split())
        if len(compact) <= 180:
            return compact
        return f"{compact[:177]}..."
