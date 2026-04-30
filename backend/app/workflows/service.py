from ..core.schemas import (
    ActorContext,
    AgentRunRequest,
    WorkflowName,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStepResult,
)
from ..orchestration.agent_router import AgentRouter
from .registry import WorkflowRegistry


class WorkflowService:
    def __init__(self, agent_router: AgentRouter, registry: WorkflowRegistry) -> None:
        self.agent_router = agent_router
        self.registry = registry

    def run(
        self,
        workflow_name: WorkflowName,
        request: WorkflowRunRequest,
        actor: ActorContext,
    ) -> WorkflowRunResponse:
        workflow = self.registry.get_workflow(workflow_name)
        agent_request = AgentRunRequest(
            agent_type=workflow.mapped_agent_type,
            document_text=request.document_text,
            provider=request.provider,
            metadata=request.metadata,
            use_retrieval=request.use_retrieval,
        )
        agent_result = self.agent_router.run(
            request=agent_request,
            actor=actor,
            workflow_name=workflow_name,
        )

        steps: list[WorkflowStepResult] = []
        for step in workflow.steps:
            if step.id == "validate":
                missing = [
                    key for key, value in agent_result.extracted_fields.items() if value in (None, "")
                ]
                steps.append(
                    WorkflowStepResult(
                        id=step.id,
                        action=step.action,
                        status="flagged" if missing else "completed",
                        detail=(
                            f"Missing or incomplete fields detected: {', '.join(missing[:5])}."
                            if missing
                            else "Required fields are populated for downstream handling."
                        ),
                    )
                )
                continue

            if step.id == "approve_high_value":
                is_high_value = agent_result.routing_target == "finance.ap_high_value"
                steps.append(
                    WorkflowStepResult(
                        id=step.id,
                        action=step.action,
                        status="completed" if is_high_value else "skipped",
                        detail=(
                            "Invoice exceeds the approval threshold and is ready for finance approval."
                            if is_high_value
                            else "High-value approval not required for this invoice."
                        ),
                    )
                )
                continue

            if step.id == "medical_review":
                requires_medical_review = agent_result.routing_target == "healthcare.medical_review"
                steps.append(
                    WorkflowStepResult(
                        id=step.id,
                        action=step.action,
                        status="completed" if requires_medical_review else "skipped",
                        detail=(
                            "Service complexity triggered medical review."
                            if requires_medical_review
                            else "Case remains in standard utilization review."
                        ),
                    )
                )
                continue

            if step.id in {"route", "utilization_review"}:
                steps.append(
                    WorkflowStepResult(
                        id=step.id,
                        action=step.action,
                        status="completed",
                        detail=f"Workflow routed to {agent_result.routing_target}.",
                    )
                )
                continue

            if step.id == "eligibility":
                steps.append(
                    WorkflowStepResult(
                        id=step.id,
                        action=step.action,
                        status="completed",
                        detail="Eligibility and payer-rule validation instructions were attached to next actions.",
                    )
                )
                continue

            steps.append(
                WorkflowStepResult(
                    id=step.id,
                    action=step.action,
                    status="completed",
                    detail="Step completed in the starter workflow path.",
                )
            )

        status = "completed_with_flags" if any(step.status == "flagged" for step in steps) else "completed"
        return WorkflowRunResponse(
            workflow_name=workflow.name,
            workflow_version=workflow.version,
            status=status,
            steps=steps,
            agent_result=agent_result,
        )
