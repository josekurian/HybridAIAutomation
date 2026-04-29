from typing import Any, Literal

from pydantic import BaseModel, Field

AgentType = Literal["invoice", "prior_authorization"]
ProviderType = Literal["local", "openai", "oci"]


class RetrievedContext(BaseModel):
    source: str
    excerpt: str
    relevance: float = Field(ge=0.0, le=1.0)


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
    processing_notes: list[str] = Field(default_factory=list)
