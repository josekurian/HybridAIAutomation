from ..core.schemas import AgentRunResponse, IntegrationResult, MCPToolCallResponse


class OracleERPClient:
    def build_invoice_actions(
        self,
        result: AgentRunResponse,
        tool_calls: list[MCPToolCallResponse],
    ) -> list[IntegrationResult]:
        supplier_lookup = next((call for call in tool_calls if call.tool.name == "oracle_erp_supplier_lookup"), None)
        invoice_import = next((call for call in tool_calls if call.tool.name == "oracle_erp_ap_invoice_import"), None)
        return [
            IntegrationResult(
                system="oracle_erp",
                action="supplier_lookup",
                status="simulated" if supplier_lookup else "not_applicable",
                reference=supplier_lookup.reference if supplier_lookup else None,
                details=supplier_lookup.output if supplier_lookup else {},
            ),
            IntegrationResult(
                system="oracle_erp",
                action="ap_invoice_intake",
                status="prepared" if invoice_import else "not_applicable",
                reference=invoice_import.reference if invoice_import else None,
                details=invoice_import.output if invoice_import else {},
            ),
        ]
