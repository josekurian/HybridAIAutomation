import re
from decimal import Decimal, InvalidOperation

from ..core.schemas import AgentRunResponse, DecisionTraceItem, RetrievedContext


class InvoiceAgent:
    def analyze(self, document_text: str, context: list[RetrievedContext]) -> AgentRunResponse:
        normalized = " ".join(document_text.split())
        invoice_number = self._extract(
            r"(?:invoice(?:\s+number|\s+no\.?|\s*#)?[:\s]+)([A-Z0-9-]+)",
            normalized,
        )
        vendor = self._extract(
            r"(?:vendor|supplier|invoice from)[:\s]+([A-Za-z0-9&.,\-\s]+?)(?:amount|total|due|invoice|po|$)",
            normalized,
        )
        amount_text = self._extract(
            r"(?:amount due|balance due|total due|invoice total|total)[:\s$]+([0-9,]+\.\d{2})",
            normalized,
        )
        due_date = self._extract(
            r"(?:due date|payment due)[:\s]+([A-Za-z0-9,/\- ]+?)(?:po|purchase order|amount|$)",
            normalized,
        )
        po_number = self._extract(
            r"(?:po|purchase order)(?:\s+number|\s+no\.?|\s*#)?[:\s]+([A-Z0-9-]+)",
            normalized,
        )

        amount_value = self._parse_amount(amount_text)
        extracted_fields = {
            "invoice_number": invoice_number,
            "vendor": self._clean(vendor),
            "amount_due": amount_text,
            "due_date": self._clean(due_date),
            "purchase_order_number": po_number,
        }

        missing_critical = [
            name
            for name in ("invoice_number", "amount_due", "due_date")
            if not extracted_fields.get(name)
        ]
        decision_trace = [
            DecisionTraceItem(
                step="extraction",
                detail=(
                    "Parsed invoice number, vendor, amount, due date, and purchase order from the document text."
                ),
            )
        ]

        next_actions = []
        if missing_critical:
            next_actions.append(
                f"Review OCR or source document for missing fields: {', '.join(missing_critical)}."
            )
            decision_trace.append(
                DecisionTraceItem(
                    step="validation",
                    detail=f"Missing critical invoice fields were detected: {', '.join(missing_critical)}.",
                )
            )
        if amount_value is not None and amount_value >= Decimal("10000"):
            next_actions.append("Escalate to finance approval because the amount exceeds $10,000.")
            routing_target = "finance.ap_high_value"
            decision_trace.append(
                DecisionTraceItem(
                    step="approval_threshold",
                    detail="Amount due met the high-value threshold, so the invoice was escalated for finance approval.",
                )
            )
        else:
            next_actions.append("Route to accounts payable for standard validation and posting.")
            routing_target = "finance.ap_standard"
            decision_trace.append(
                DecisionTraceItem(
                    step="approval_threshold",
                    detail="Amount due stayed below the high-value threshold, so the invoice remained in the standard AP queue.",
                )
            )
        if po_number:
            next_actions.append("Match the invoice against the purchase order before posting.")
            decision_trace.append(
                DecisionTraceItem(
                    step="po_matching",
                    detail=f"Purchase order {po_number} was found, so PO matching is required before posting.",
                )
            )
        else:
            next_actions.append("Request a PO reference or confirm the invoice is non-PO spend.")
            decision_trace.append(
                DecisionTraceItem(
                    step="po_matching",
                    detail="No purchase order reference was found, so the operator must confirm non-PO handling or add the PO.",
                )
            )

        summary_vendor = extracted_fields["vendor"] or "an unknown vendor"
        summary_amount = extracted_fields["amount_due"] or "an unspecified amount"
        summary_due = extracted_fields["due_date"] or "an unspecified date"
        summary = f"Invoice {invoice_number or 'unidentified'} from {summary_vendor} for ${summary_amount} due {summary_due}."

        confidence = max(0.45, 0.9 - (0.15 * len(missing_critical)))
        if context:
            confidence = min(0.97, confidence + 0.03)

        return AgentRunResponse(
            agent_type="invoice",
            provider="local",
            status="completed",
            summary=summary,
            extracted_fields=extracted_fields,
            next_actions=next_actions,
            routing_target=routing_target,
            confidence=round(confidence, 2),
            retrieved_context=context,
            decision_trace=decision_trace,
        )

    @staticmethod
    def _extract(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip()

    @staticmethod
    def _parse_amount(amount_text: str | None) -> Decimal | None:
        if not amount_text:
            return None
        try:
            return Decimal(amount_text.replace(",", ""))
        except InvalidOperation:
            return None

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if not value:
            return None
        return re.sub(r"\s+", " ", value).strip(" .,-")
