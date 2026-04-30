from ..core.schemas import AgentRunResponse, IntegrationResult, MCPToolCallResponse


class OracleHealthClient:
    def build_prior_auth_actions(
        self,
        result: AgentRunResponse,
        tool_calls: list[MCPToolCallResponse],
    ) -> list[IntegrationResult]:
        eligibility = next((call for call in tool_calls if call.tool.name == "oracle_health_eligibility_check"), None)
        prior_auth_case = next(
            (call for call in tool_calls if call.tool.name == "oracle_health_prior_auth_case_create"),
            None,
        )
        return [
            IntegrationResult(
                system="oracle_health",
                action="eligibility_check_stub",
                status="simulated" if eligibility else "not_applicable",
                reference=eligibility.reference if eligibility else None,
                details=eligibility.output if eligibility else {},
            ),
            IntegrationResult(
                system="oracle_health",
                action="prior_auth_case_stub",
                status="prepared" if prior_auth_case else "not_applicable",
                reference=prior_auth_case.reference if prior_auth_case else None,
                details=prior_auth_case.output if prior_auth_case else {},
            ),
        ]
