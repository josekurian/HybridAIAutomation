from ..core.schemas import AgentRunResponse, MultiAgentExecution, SpecialistFinding, TeamHandoff, TeamMember


class TeamOrchestrator:
    def build_execution(self, result: AgentRunResponse) -> MultiAgentExecution:
        if result.agent_type == "invoice":
            return self._build_invoice_execution(result)
        return self._build_prior_auth_execution(result)

    def _build_invoice_execution(self, result: AgentRunResponse) -> MultiAgentExecution:
        po_number = result.extracted_fields.get("purchase_order_number")
        has_high_value_route = result.routing_target == "finance.ap_high_value"
        findings = [
            SpecialistFinding(
                agent_id="invoice-intake-analyst",
                title="Invoice parsed",
                detail="Core AP fields were extracted from the incoming document.",
            ),
            SpecialistFinding(
                agent_id="duplicate-risk-agent",
                title="Duplicate risk posture",
                detail=(
                    "Document includes duplicate-risk language and should be reviewed for repeated supplier submissions."
                    if "duplicate" in result.summary.lower() or any(
                        "duplicate" in action.lower() for action in result.next_actions
                    )
                    else "No direct duplicate keyword was found in the starter analysis."
                ),
                severity="warning" if any("duplicate" in action.lower() for action in result.next_actions) else "info",
            ),
            SpecialistFinding(
                agent_id="oracle-ap-handoff-agent",
                title="Oracle AP readiness",
                detail=(
                    f"Supplier and invoice handoff artifacts are ready for route {result.routing_target}."
                ),
            ),
        ]
        return MultiAgentExecution(
            team_id="team_finance_invoice_ops",
            team_name="Finance Invoice Operations Team",
            orchestration_mode="supervisor",
            members=[
                TeamMember(
                    agent_id="invoice-intake-analyst",
                    name="Invoice Intake Analyst",
                    role="Normalize invoice content and extract AP fields",
                    status="completed",
                    notes=["Normalized OCR-style text and extracted invoice, vendor, amount, and due date."],
                ),
                TeamMember(
                    agent_id="policy-validation-agent",
                    name="Policy Validation Agent",
                    role="Apply AP threshold and PO matching rules",
                    status="completed",
                    notes=["Applied approval threshold and PO validation checks."],
                ),
                TeamMember(
                    agent_id="duplicate-risk-agent",
                    name="Duplicate Risk Agent",
                    role="Screen for duplicate invoices and payment risk signals",
                    status="completed",
                    notes=["Starter duplicate review executed through heuristic findings."],
                ),
                TeamMember(
                    agent_id="oracle-ap-handoff-agent",
                    name="Oracle AP Handoff Agent",
                    role="Prepare REST handoff artifacts for Oracle Payables",
                    status="completed",
                    notes=["Generated simulated supplier lookup and AP invoice import artifacts."],
                ),
            ],
            handoffs=[
                TeamHandoff(
                    from_agent="invoice-intake-analyst",
                    to_agent="policy-validation-agent",
                    reason="Core AP fields are ready for threshold and policy checks.",
                    status="completed",
                ),
                TeamHandoff(
                    from_agent="policy-validation-agent",
                    to_agent="duplicate-risk-agent",
                    reason="Validated invoice should be screened for duplicate and exception signals.",
                    status="completed",
                ),
                TeamHandoff(
                    from_agent="duplicate-risk-agent",
                    to_agent="oracle-ap-handoff-agent",
                    reason="Oracle AP handoff requires the validated route and risk posture.",
                    status="completed",
                ),
            ],
            findings=findings + [
                SpecialistFinding(
                    agent_id="policy-validation-agent",
                    title="PO match requirement",
                    detail=(
                        f"Purchase order {po_number} will require invoice matching before posting."
                        if po_number
                        else "No purchase order was found; non-PO confirmation remains required."
                    ),
                    severity="warning" if not po_number else "info",
                ),
                SpecialistFinding(
                    agent_id="policy-validation-agent",
                    title="Approval outcome",
                    detail=(
                        "Invoice exceeded the configured threshold and requires finance approval."
                        if has_high_value_route
                        else "Invoice remained in standard AP validation."
                    ),
                    severity="critical" if has_high_value_route else "info",
                ),
            ],
        )

    def _build_prior_auth_execution(self, result: AgentRunResponse) -> MultiAgentExecution:
        is_medical_review = result.routing_target == "healthcare.medical_review"
        return MultiAgentExecution(
            team_id="team_prior_auth_command",
            team_name="Prior Authorization Command Team",
            orchestration_mode="supervisor",
            members=[
                TeamMember(
                    agent_id="intake-navigator-agent",
                    name="Intake Navigator Agent",
                    role="Capture member and clinical request details",
                    status="completed",
                    notes=["Parsed patient, member, payer, diagnosis, and procedure details."],
                ),
                TeamMember(
                    agent_id="eligibility-review-agent",
                    name="Eligibility Review Agent",
                    role="Check completeness and payer rule readiness",
                    status="completed",
                    notes=["Prepared eligibility and coverage confirmation actions."],
                ),
                TeamMember(
                    agent_id="medical-necessity-agent",
                    name="Medical Necessity Agent",
                    role="Determine if the request needs escalation to medical review",
                    status="completed",
                    notes=["Applied starter medical-review trigger logic."],
                ),
                TeamMember(
                    agent_id="oracle-health-handoff-agent",
                    name="Oracle Health Handoff Agent",
                    role="Prepare prior authorization REST handoff artifacts",
                    status="completed",
                    notes=["Generated simulated eligibility and prior-auth case artifacts."],
                ),
            ],
            handoffs=[
                TeamHandoff(
                    from_agent="intake-navigator-agent",
                    to_agent="eligibility-review-agent",
                    reason="Structured request details are ready for payer and completeness review.",
                    status="completed",
                ),
                TeamHandoff(
                    from_agent="eligibility-review-agent",
                    to_agent="medical-necessity-agent",
                    reason="Clinical request is ready for acuity and medical-review screening.",
                    status="completed",
                ),
                TeamHandoff(
                    from_agent="medical-necessity-agent",
                    to_agent="oracle-health-handoff-agent",
                    reason="Final routing target must be carried into Oracle Health artifacts.",
                    status="completed",
                ),
            ],
            findings=[
                SpecialistFinding(
                    agent_id="eligibility-review-agent",
                    title="Coverage validation required",
                    detail="Benefit coverage and payer-specific authorization checks remain part of the next action bundle.",
                ),
                SpecialistFinding(
                    agent_id="medical-necessity-agent",
                    title="Medical review posture",
                    detail=(
                        "Request matched a higher-acuity rule and was escalated to medical review."
                        if is_medical_review
                        else "Request stayed in standard utilization review."
                    ),
                    severity="critical" if is_medical_review else "info",
                ),
                SpecialistFinding(
                    agent_id="oracle-health-handoff-agent",
                    title="Oracle Health case readiness",
                    detail=f"Oracle Health case payload is ready for queue {result.routing_target}.",
                ),
            ],
        )
