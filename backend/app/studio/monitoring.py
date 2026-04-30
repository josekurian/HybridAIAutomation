from collections import Counter
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from ..core.schemas import MonitoringSnapshot


class MonitoringService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._events: list[dict[str, Any]] = []

    def record_run(
        self,
        *,
        workflow_name: str | None,
        agent_type: str,
        provider: str,
        latency_ms: float,
        status: str,
        input_tokens: int,
        output_tokens: int,
        routing_target: str,
    ) -> None:
        event = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "workflow_name": workflow_name or agent_type,
            "agent_type": agent_type,
            "provider": provider,
            "latency_ms": round(latency_ms, 2),
            "status": status,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "routing_target": routing_target,
        }
        with self._lock:
            self._events.append(event)
            self._events = self._events[-100:]

    def snapshot(self) -> MonitoringSnapshot:
        with self._lock:
            events = list(self._events)

        total_runs = len(events)
        success_count = sum(1 for event in events if str(event["status"]).startswith("completed"))
        latency = sum(float(event["latency_ms"]) for event in events)
        input_tokens = sum(int(event["input_tokens"]) for event in events)
        output_tokens = sum(int(event["output_tokens"]) for event in events)
        workflow_counts = Counter(str(event["workflow_name"]) for event in events)
        provider_counts = Counter(str(event["provider"]) for event in events)
        success_rate = (success_count / total_runs) if total_runs else 1.0
        error_rate = 1.0 - success_rate if total_runs else 0.0
        average_latency = (latency / total_runs) if total_runs else 0.0

        return MonitoringSnapshot(
            generated_at=datetime.now(UTC),
            total_runs=total_runs,
            success_rate=round(success_rate, 2),
            average_latency_ms=round(average_latency, 2),
            error_rate=round(error_rate, 2),
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            runs_by_workflow=dict(workflow_counts),
            runs_by_provider=dict(provider_counts),
            recent_events=events[-8:],
        )
