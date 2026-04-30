from pathlib import Path

import yaml

from ..core.schemas import AgentType, WorkflowDefinition, WorkflowName, WorkflowStepDefinition


class WorkflowRegistry:
    agent_mapping: dict[WorkflowName, AgentType] = {
        "invoice_processing": "invoice",
        "prior_authorization": "prior_authorization",
    }

    def __init__(self) -> None:
        self._workflows_dir = self._discover_workflows_dir()

    def list_workflows(self) -> list[WorkflowDefinition]:
        return [
            self.get_workflow("invoice_processing"),
            self.get_workflow("prior_authorization"),
        ]

    def get_workflow(self, workflow_name: WorkflowName) -> WorkflowDefinition:
        path = self._workflows_dir / f"{workflow_name}.yaml"
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        version = int(raw.get("version", 1))
        steps = [
            WorkflowStepDefinition(
                id=step["id"],
                action=step["action"],
                agent=step.get("agent"),
                target=step.get("target"),
                when=step.get("when"),
            )
            for step in raw.get("steps", [])
        ]
        return WorkflowDefinition(
            name=workflow_name,
            version=version,
            description=str(raw.get("description", "")),
            mapped_agent_type=self.agent_mapping[workflow_name],
            steps=steps,
        )

    def _discover_workflows_dir(self) -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            candidate = parent / "workflows"
            if (
                candidate.is_dir()
                and (candidate / "invoice_processing.yaml").is_file()
                and (candidate / "prior_authorization.yaml").is_file()
            ):
                return candidate
        raise RuntimeError("Unable to locate workflows directory.")
