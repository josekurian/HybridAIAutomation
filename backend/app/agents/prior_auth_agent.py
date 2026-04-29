import re

from ..core.schemas import AgentRunResponse, RetrievedContext


class PriorAuthAgent:
    def analyze(self, document_text: str, context: list[RetrievedContext]) -> AgentRunResponse:
        normalized = " ".join(document_text.split())
        patient_name = self._extract(
            r"(?:patient|member name)[:\s]+([A-Za-z ,.'-]+?)(?:member id|payer|diagnosis|procedure|$)",
            normalized,
        )
        member_id = self._extract(
            r"(?:member id|subscriber id|policy id)[:\s]+([A-Z0-9-]+)",
            normalized,
        )
        payer = self._extract(
            r"(?:payer|insurance|health plan)[:\s]+([A-Za-z0-9&.,\-\s]+?)(?:diagnosis|procedure|cpt|member|$)",
            normalized,
        )
        diagnosis = self._extract(
            r"(?:diagnosis|dx)[:\s]+([A-Za-z0-9 ,.\-()]+?)(?:procedure|cpt|service date|$)",
            normalized,
        )
        procedure = self._extract(
            r"(?:procedure|requested service|cpt)[:\s]+([A-Za-z0-9 ,.\-()]+?)(?:diagnosis|service date|provider|$)",
            normalized,
        )
        ordering_provider = self._extract(
            r"(?:ordering provider|requesting provider|physician)[:\s]+([A-Za-z ,.'-]+?)(?:service date|notes|$)",
            normalized,
        )

        extracted_fields = {
            "patient_name": self._clean(patient_name),
            "member_id": member_id,
            "payer": self._clean(payer),
            "diagnosis": self._clean(diagnosis),
            "procedure": self._clean(procedure),
            "ordering_provider": self._clean(ordering_provider),
        }

        missing_critical = [
            name
            for name in ("patient_name", "member_id", "payer", "diagnosis", "procedure")
            if not extracted_fields.get(name)
        ]

        high_review_keywords = ("surgery", "inpatient", "oncology", "infusion", "mri")
        requires_medical_review = any(keyword in normalized.lower() for keyword in high_review_keywords)

        next_actions = []
        if missing_critical:
            next_actions.append(
                f"Request missing utilization review inputs: {', '.join(missing_critical)}."
            )
        next_actions.append("Confirm benefit coverage and payer-specific authorization rules.")
        next_actions.append("Validate diagnosis-to-procedure alignment before submission.")

        if requires_medical_review:
            routing_target = "healthcare.medical_review"
            next_actions.append("Escalate to medical review due to service complexity.")
        else:
            routing_target = "healthcare.utilization_review"
            next_actions.append("Route to utilization review for standard prior auth handling.")

        summary = (
            f"Prior authorization request for {extracted_fields['patient_name'] or 'an unidentified patient'} "
            f"with payer {extracted_fields['payer'] or 'unknown payer'} for "
            f"{extracted_fields['procedure'] or 'an unspecified procedure'}."
        )

        confidence = max(0.4, 0.88 - (0.1 * len(missing_critical)))
        if context:
            confidence = min(0.96, confidence + 0.04)

        return AgentRunResponse(
            agent_type="prior_authorization",
            provider="local",
            status="completed",
            summary=summary,
            extracted_fields=extracted_fields,
            next_actions=next_actions,
            routing_target=routing_target,
            confidence=round(confidence, 2),
            retrieved_context=context,
        )

    @staticmethod
    def _extract(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip()

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if not value:
            return None
        return re.sub(r"\s+", " ", value).strip(" .,-")
