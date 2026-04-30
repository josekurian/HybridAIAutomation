from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from ..core.schemas import MCPServerContract, MCPToolCallResponse, MCPToolContract


class MCPRuntime:
    def __init__(self) -> None:
        self._servers = [
            MCPServerContract(
                server_label="oracle_erp",
                server_description="Local Oracle ERP MCP-compatible runtime for supplier and AP invoice actions.",
                server_url="local://oracle_erp",
                require_approval="always",
                allowed_tools=["oracle_erp_supplier_lookup", "oracle_erp_ap_invoice_import"],
            ),
            MCPServerContract(
                server_label="oracle_health",
                server_description="Local Oracle Health MCP-compatible runtime for eligibility and prior auth actions.",
                server_url="local://oracle_health",
                require_approval="always",
                allowed_tools=["oracle_health_eligibility_check", "oracle_health_prior_auth_case_create"],
            ),
        ]
        self._tools = [
            MCPToolContract(
                server_label="oracle_erp",
                name="oracle_erp_supplier_lookup",
                description="Look up supplier details in Oracle ERP using supplier name or supplier number.",
                parameters={
                    "type": "object",
                    "properties": {
                        "vendor": {"type": "string"},
                        "supplier_number": {"type": "string"},
                    },
                    "required": ["vendor"],
                    "additionalProperties": False,
                },
                tags=["oracle", "finance", "supplier", "mcp"],
                require_approval="always",
            ),
            MCPToolContract(
                server_label="oracle_erp",
                name="oracle_erp_ap_invoice_import",
                description="Prepare an Oracle ERP Payables invoice import payload.",
                parameters={
                    "type": "object",
                    "properties": {
                        "invoice_number": {"type": "string"},
                        "amount_due": {"type": "string"},
                        "routing_target": {"type": "string"},
                        "purchase_order_number": {"type": "string"},
                    },
                    "required": ["invoice_number", "amount_due", "routing_target"],
                    "additionalProperties": False,
                },
                tags=["oracle", "finance", "payables", "mcp"],
                require_approval="always",
            ),
            MCPToolContract(
                server_label="oracle_health",
                name="oracle_health_eligibility_check",
                description="Prepare a payer eligibility request for an Oracle Health-connected workflow.",
                parameters={
                    "type": "object",
                    "properties": {
                        "member_id": {"type": "string"},
                        "payer": {"type": "string"},
                        "patient_name": {"type": "string"},
                    },
                    "required": ["member_id", "payer"],
                    "additionalProperties": False,
                },
                tags=["oracle", "healthcare", "eligibility", "mcp"],
                require_approval="always",
            ),
            MCPToolContract(
                server_label="oracle_health",
                name="oracle_health_prior_auth_case_create",
                description="Prepare an Oracle Health prior authorization case payload.",
                parameters={
                    "type": "object",
                    "properties": {
                        "member_id": {"type": "string"},
                        "procedure": {"type": "string"},
                        "diagnosis": {"type": "string"},
                        "routing_target": {"type": "string"},
                    },
                    "required": ["member_id", "procedure", "routing_target"],
                    "additionalProperties": False,
                },
                tags=["oracle", "healthcare", "prior_auth", "mcp"],
                require_approval="always",
            ),
        ]

    def list_servers(self) -> list[MCPServerContract]:
        return list(self._servers)

    def list_tools(self) -> list[MCPToolContract]:
        return list(self._tools)

    def get_tool(self, tool_name: str) -> MCPToolContract:
        for tool in self._tools:
            if tool.name == tool_name:
                return tool
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP tool not found.")

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolCallResponse:
        tool = self.get_tool(tool_name)
        handlers = {
            "oracle_erp_supplier_lookup": self._oracle_erp_supplier_lookup,
            "oracle_erp_ap_invoice_import": self._oracle_erp_ap_invoice_import,
            "oracle_health_eligibility_check": self._oracle_health_eligibility_check,
            "oracle_health_prior_auth_case_create": self._oracle_health_prior_auth_case_create,
        }
        output = handlers[tool_name](arguments)
        return MCPToolCallResponse(
            tool=tool,
            status="completed",
            arguments=arguments,
            output=output,
            reference=str(output.get("reference")) if output.get("reference") else None,
            notes=[f"Executed through local MCP runtime {tool.server_label}."],
        )

    def _oracle_erp_supplier_lookup(self, arguments: dict[str, Any]) -> dict[str, Any]:
        vendor = str(arguments.get("vendor") or "UNKNOWN").upper().replace(" ", "-")
        return {
            "reference": f"SUP-{vendor[:18]}",
            "matched_vendor_name": arguments.get("vendor"),
            "oracle_module": "Payables",
        }

    def _oracle_erp_ap_invoice_import(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "reference": f"ERP-INV-{uuid4().hex[:10]}",
            "routing_target": arguments.get("routing_target"),
            "amount_due": arguments.get("amount_due"),
            "purchase_order_number": arguments.get("purchase_order_number"),
            "status": "prepared",
        }

    def _oracle_health_eligibility_check(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "reference": f"ELIG-{uuid4().hex[:10]}",
            "member_id": arguments.get("member_id"),
            "payer": arguments.get("payer"),
            "status": "simulated",
        }

    def _oracle_health_prior_auth_case_create(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "reference": f"PA-{uuid4().hex[:10]}",
            "member_id": arguments.get("member_id"),
            "procedure": arguments.get("procedure"),
            "diagnosis": arguments.get("diagnosis"),
            "queue": arguments.get("routing_target"),
            "status": "prepared",
        }
