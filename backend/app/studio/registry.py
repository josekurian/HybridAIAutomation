from ..core.schemas import (
    AgentTemplate,
    MarketplaceItem,
    RestIntegrationDefinition,
    SampleUseCase,
    TemplateFieldDefinition,
)


class StudioRegistry:
    def __init__(self) -> None:
        self._templates = [
            AgentTemplate(
                template_id="invoice-oracle-ap-supervisor",
                name="Oracle AP Invoice Supervisor",
                domain="finance",
                mapped_agent_type="invoice",
                summary="Coordinates intake, policy validation, duplicate review, and Oracle AP handoff.",
                natural_language_prompt=(
                    "Review invoice intake, validate critical AP fields, detect risk signals, "
                    "and prepare Oracle Payables handoff guidance with explainable next actions."
                ),
                orchestration_mode="supervisor",
                data_sources=["invoice_document", "supplier_master", "po_reference", "ap_policy_knowledge"],
                tools=["supplier_lookup", "po_match_check", "duplicate_scan", "rest_api_handoff"],
                sample_use_case_ids=["invoice-high-value-escalation", "invoice-duplicate-risk-review"],
                fields=[
                    TemplateFieldDefinition(name="invoice_number", label="Invoice Number", example="INV-2026-041"),
                    TemplateFieldDefinition(name="vendor", label="Vendor", example="Northwind Medical Supplies"),
                    TemplateFieldDefinition(name="amount_due", label="Amount Due", example="12480.00"),
                    TemplateFieldDefinition(name="due_date", label="Due Date", example="2026-05-15"),
                    TemplateFieldDefinition(name="purchase_order_number", label="PO Number", required=False, example="PO-88412"),
                ],
                tags=["oracle_erp", "accounts_payable", "supervisor", "rest_api"],
            ),
            AgentTemplate(
                template_id="invoice-low-code-exception-studio",
                name="Invoice Exception Studio",
                domain="finance",
                mapped_agent_type="invoice",
                summary="Low-code blueprint for AP exception handling and payment hold resolution.",
                natural_language_prompt=(
                    "Detect invoice completeness, exception risk, and payment hold conditions, "
                    "then route the case to the correct AP queue."
                ),
                orchestration_mode="sequential",
                data_sources=["invoice_document", "payment_holds", "supplier_policy_rules"],
                tools=["hold_reason_lookup", "exception_classifier", "rest_api_handoff"],
                sample_use_case_ids=["invoice-payment-hold-followup"],
                fields=[
                    TemplateFieldDefinition(name="invoice_number", label="Invoice Number"),
                    TemplateFieldDefinition(name="vendor", label="Vendor"),
                    TemplateFieldDefinition(name="amount_due", label="Amount Due"),
                ],
                tags=["low_code", "exceptions", "oracle_erp"],
            ),
            AgentTemplate(
                template_id="prior-auth-supervisor",
                name="Prior Authorization Supervisor",
                domain="healthcare",
                mapped_agent_type="prior_authorization",
                summary="Coordinates intake, eligibility review, medical necessity screening, and Oracle Health case creation.",
                natural_language_prompt=(
                    "Review prior authorization requests, validate core member and clinical data, "
                    "screen for medical-review triggers, and prepare Oracle Health routing artifacts."
                ),
                orchestration_mode="supervisor",
                data_sources=["clinical_request", "payer_policy_rules", "eligibility_stub", "fhir_summary"],
                tools=["eligibility_check", "medical_review_trigger", "rest_api_handoff", "fhir_bridge"],
                sample_use_case_ids=["prior-auth-mri-escalation", "prior-auth-standard-review"],
                fields=[
                    TemplateFieldDefinition(name="patient_name", label="Patient Name"),
                    TemplateFieldDefinition(name="member_id", label="Member ID"),
                    TemplateFieldDefinition(name="payer", label="Payer"),
                    TemplateFieldDefinition(name="diagnosis", label="Diagnosis"),
                    TemplateFieldDefinition(name="procedure", label="Procedure"),
                    TemplateFieldDefinition(name="ordering_provider", label="Ordering Provider", required=False),
                ],
                tags=["oracle_health", "utilization_management", "fhir", "supervisor"],
            ),
            AgentTemplate(
                template_id="prior-auth-denial-recovery",
                name="Prior Auth Denial Recovery",
                domain="healthcare",
                mapped_agent_type="prior_authorization",
                summary="Blueprint for re-review, appeal packet preparation, and payer follow-up.",
                natural_language_prompt=(
                    "Analyze denied or incomplete prior authorization requests, identify missing evidence, "
                    "and prepare a payer-ready recovery path."
                ),
                orchestration_mode="parallel_review",
                data_sources=["denial_letter", "clinical_request", "payer_policy_rules"],
                tools=["appeal_packet", "payer_rule_lookup", "rest_api_handoff"],
                sample_use_case_ids=["prior-auth-denial-recovery"],
                fields=[
                    TemplateFieldDefinition(name="member_id", label="Member ID"),
                    TemplateFieldDefinition(name="payer", label="Payer"),
                    TemplateFieldDefinition(name="diagnosis", label="Diagnosis"),
                    TemplateFieldDefinition(name="procedure", label="Procedure"),
                ],
                tags=["denials", "parallel_review", "oracle_health"],
            ),
        ]
        self._sample_use_cases = [
            SampleUseCase(
                use_case_id="invoice-high-value-escalation",
                title="High-value invoice requiring finance approval",
                domain="finance",
                template_id="invoice-oracle-ap-supervisor",
                workflow_name="invoice_processing",
                expected_route="finance.ap_high_value",
                sample_document_text=(
                    "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies "
                    "Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
                ),
                enabled_capabilities=[
                    "template_library",
                    "multi_agent_orchestration",
                    "rest_api_integration",
                    "monitoring_dashboard",
                ],
                outcome_summary="Escalates a high-value AP invoice and prepares Oracle Payables handoff artifacts.",
            ),
            SampleUseCase(
                use_case_id="invoice-duplicate-risk-review",
                title="Potential duplicate supplier invoice review",
                domain="finance",
                template_id="invoice-oracle-ap-supervisor",
                workflow_name="invoice_processing",
                expected_route="finance.ap_standard",
                sample_document_text=(
                    "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies "
                    "Amount Due: 2480.00 Due Date: 2026-05-15 PO Number: PO-88412 "
                    "Notes: duplicate copy received from supplier inbox."
                ),
                enabled_capabilities=[
                    "validation_testing",
                    "monitoring_dashboard",
                    "rest_api_integration",
                ],
                outcome_summary="Flags duplicate-risk findings while keeping the invoice in AP review.",
            ),
            SampleUseCase(
                use_case_id="invoice-payment-hold-followup",
                title="Invoice payment hold investigation",
                domain="finance",
                template_id="invoice-low-code-exception-studio",
                workflow_name="invoice_processing",
                expected_route="finance.ap_standard",
                sample_document_text=(
                    "Invoice Number: INV-2026-219 Vendor: Blue Harbor Logistics "
                    "Amount Due: 4510.00 Due Date: 2026-05-30 Notes: invoice on payment hold pending receiving confirmation."
                ),
                enabled_capabilities=[
                    "low_code_builder",
                    "credential_store",
                    "rest_api_integration",
                ],
                outcome_summary="Shows a low-code AP exception blueprint with hold-resolution follow-up.",
            ),
            SampleUseCase(
                use_case_id="prior-auth-mri-escalation",
                title="MRI request requiring medical review",
                domain="healthcare",
                template_id="prior-auth-supervisor",
                workflow_name="prior_authorization",
                expected_route="healthcare.medical_review",
                sample_document_text=(
                    "Patient: Elena Carter Member ID: MBR-55291 Payer: Evergreen Health Plan "
                    "Diagnosis: Lumbar radiculopathy Procedure: MRI lumbar spine "
                    "Ordering Provider: Dr. Ravi Patel"
                ),
                enabled_capabilities=[
                    "template_library",
                    "multi_agent_orchestration",
                    "rest_api_integration",
                    "monitoring_dashboard",
                ],
                outcome_summary="Escalates a higher-acuity imaging request and prepares Oracle Health case metadata.",
            ),
            SampleUseCase(
                use_case_id="prior-auth-standard-review",
                title="Standard utilization review request",
                domain="healthcare",
                template_id="prior-auth-supervisor",
                workflow_name="prior_authorization",
                expected_route="healthcare.utilization_review",
                sample_document_text=(
                    "Patient: Jordan Kim Member ID: MBR-99210 Payer: Evergreen Health Plan "
                    "Diagnosis: Tendon strain Procedure: Physical therapy Ordering Provider: Dr. Amy Chen"
                ),
                enabled_capabilities=[
                    "validation_testing",
                    "credential_store",
                    "rest_api_integration",
                ],
                outcome_summary="Routes a lower-acuity request into standard utilization review.",
            ),
            SampleUseCase(
                use_case_id="prior-auth-denial-recovery",
                title="Prior authorization denial recovery packet",
                domain="healthcare",
                template_id="prior-auth-denial-recovery",
                workflow_name="prior_authorization",
                expected_route="healthcare.utilization_review",
                sample_document_text=(
                    "Patient: Maya Singh Member ID: MBR-67219 Payer: Sunrise Payer Services "
                    "Diagnosis: Migraine Procedure: Infusion therapy Denial reason: insufficient documentation."
                ),
                enabled_capabilities=[
                    "marketplace_access",
                    "parallel_review",
                    "validation_testing",
                ],
                outcome_summary="Builds a denial-recovery path with appeal-ready evidence gaps.",
            ),
        ]
        self._integrations = [
            RestIntegrationDefinition(
                integration_id="oracle-erp-supplier-lookup",
                name="Oracle ERP Supplier Lookup",
                domain="finance",
                method="GET",
                path="/fscmRestApi/resources/11.13.18.05/suppliers",
                privilege_hint="ORA_FND_TRAP_PRIV supplier inquiry",
                required_credential_scope="oracle_erp",
                sample_payload={"supplierNumber": "SUP-NORTHWIND"},
                mapped_use_case_ids=["invoice-high-value-escalation", "invoice-duplicate-risk-review"],
            ),
            RestIntegrationDefinition(
                integration_id="oracle-erp-ap-invoice-import",
                name="Oracle ERP AP Invoice Import",
                domain="finance",
                method="POST",
                path="/fscmRestApi/resources/11.13.18.05/payablesInvoices",
                privilege_hint="ORA_FND_TRAP_PRIV AP import",
                required_credential_scope="oracle_erp",
                sample_payload={"invoiceNumber": "INV-2026-041", "amount": "12480.00"},
                mapped_use_case_ids=["invoice-high-value-escalation", "invoice-payment-hold-followup"],
            ),
            RestIntegrationDefinition(
                integration_id="oracle-health-eligibility",
                name="Oracle Health Eligibility Check",
                domain="healthcare",
                method="POST",
                path="/healthcareApi/v1/eligibility/check",
                privilege_hint="Oracle Health eligibility API access",
                required_credential_scope="oracle_health",
                sample_payload={"memberId": "MBR-55291", "payer": "Evergreen Health Plan"},
                mapped_use_case_ids=["prior-auth-mri-escalation", "prior-auth-standard-review"],
            ),
            RestIntegrationDefinition(
                integration_id="oracle-health-prior-auth-case",
                name="Oracle Health Prior Authorization Case",
                domain="healthcare",
                method="POST",
                path="/healthcareApi/v1/priorAuthorization/cases",
                privilege_hint="Oracle Health prior auth case write",
                required_credential_scope="oracle_health",
                sample_payload={"memberId": "MBR-55291", "procedure": "MRI lumbar spine"},
                mapped_use_case_ids=["prior-auth-mri-escalation", "prior-auth-denial-recovery"],
            ),
        ]
        self._marketplace_items = [
            MarketplaceItem(
                item_id="mkp-oracle-ap-accelerator",
                name="Oracle AP Accelerator Pack",
                publisher="HybridAIAutomation Marketplace",
                domain="finance",
                summary="Validated AP invoice, duplicate detection, and payment-hold starter pack.",
                capabilities=[
                    "agent_template_library",
                    "multi_agent_orchestration",
                    "rest_api_integration",
                    "validation_testing",
                ],
                template_id="invoice-oracle-ap-supervisor",
                validated_for=["Invoice Processing", "Oracle ERP AP demos"],
            ),
            MarketplaceItem(
                item_id="mkp-prior-auth-accelerator",
                name="Prior Authorization Recovery Pack",
                publisher="HybridAIAutomation Marketplace",
                domain="healthcare",
                summary="Validated prior-auth, denial recovery, and Oracle Health routing starter pack.",
                capabilities=[
                    "agent_template_library",
                    "multi_agent_orchestration",
                    "rest_api_integration",
                    "marketplace_access",
                ],
                template_id="prior-auth-supervisor",
                validated_for=["Prior Authorization", "Oracle Health pilots"],
            ),
        ]

    def list_templates(self) -> list[AgentTemplate]:
        return list(self._templates)

    def get_template(self, template_id: str) -> AgentTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        raise KeyError(template_id)

    def list_use_cases(self) -> list[SampleUseCase]:
        return list(self._sample_use_cases)

    def get_use_case(self, use_case_id: str) -> SampleUseCase:
        for use_case in self._sample_use_cases:
            if use_case.use_case_id == use_case_id:
                return use_case
        raise KeyError(use_case_id)

    def list_integrations(self) -> list[RestIntegrationDefinition]:
        return list(self._integrations)

    def get_integration(self, integration_id: str) -> RestIntegrationDefinition:
        for integration in self._integrations:
            if integration.integration_id == integration_id:
                return integration
        raise KeyError(integration_id)

    def list_marketplace_items(self) -> list[MarketplaceItem]:
        return list(self._marketplace_items)

    def get_marketplace_item(self, item_id: str) -> MarketplaceItem:
        for item in self._marketplace_items:
            if item.item_id == item_id:
                return item
        raise KeyError(item_id)
