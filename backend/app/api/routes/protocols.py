from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.schemas import A2AAgentCard, MCPServerContract, MCPToolCallRequest, MCPToolCallResponse, MCPToolContract
from ...core.security import require_scopes
from ...protocols.a2a_registry import A2ARegistry
from ...protocols.mcp_runtime import MCPRuntime

router = APIRouter(prefix="/protocols", tags=["protocols"])
mcp_runtime = MCPRuntime()
a2a_registry = A2ARegistry()


@router.get("/mcp/servers", response_model=list[MCPServerContract])
def list_mcp_servers(
    actor: Annotated[object, Depends(require_scopes("protocols:mcp:read"))],
) -> list[MCPServerContract]:
    _ = actor
    return mcp_runtime.list_servers()


@router.get("/mcp/tools", response_model=list[MCPToolContract])
def list_mcp_tools(
    actor: Annotated[object, Depends(require_scopes("protocols:mcp:read"))],
) -> list[MCPToolContract]:
    _ = actor
    return mcp_runtime.list_tools()


@router.post("/mcp/tools/{tool_name}/call", response_model=MCPToolCallResponse)
def call_mcp_tool(
    tool_name: str,
    request: MCPToolCallRequest,
    actor: Annotated[object, Depends(require_scopes("protocols:mcp:execute"))],
) -> MCPToolCallResponse:
    _ = actor
    return mcp_runtime.execute_tool(tool_name, request.arguments)


@router.get("/a2a/cards", response_model=list[A2AAgentCard])
def list_a2a_cards(
    actor: Annotated[object, Depends(require_scopes("protocols:a2a:read"))],
) -> list[A2AAgentCard]:
    _ = actor
    return a2a_registry.list_cards()


@router.get("/a2a/cards/{card_id}", response_model=A2AAgentCard)
def get_a2a_card(
    card_id: str,
    actor: Annotated[object, Depends(require_scopes("protocols:a2a:read"))],
) -> A2AAgentCard:
    _ = actor
    return a2a_registry.get_card(card_id)
