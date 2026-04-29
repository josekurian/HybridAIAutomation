import re
from dataclasses import dataclass

from ..core.schemas import AgentType, RetrievedContext


@dataclass(frozen=True)
class KnowledgeSnippet:
    domain: AgentType
    source: str
    excerpt: str
    keywords: tuple[str, ...]


class DomainRetriever:
    def __init__(self) -> None:
        self.corpus = [
            KnowledgeSnippet(
                domain="invoice",
                source="ap-policy/high-value",
                excerpt="Invoices above $10,000 require finance approval before posting.",
                keywords=("invoice", "amount", "total", "approval", "finance"),
            ),
            KnowledgeSnippet(
                domain="invoice",
                source="ap-policy/matching",
                excerpt="Three-way match requires invoice, purchase order, and receiving confirmation.",
                keywords=("invoice", "purchase", "order", "po", "match", "receiving"),
            ),
            KnowledgeSnippet(
                domain="prior_authorization",
                source="payer-rules/core",
                excerpt="Prior authorization requires member eligibility, diagnosis, and requested procedure.",
                keywords=("member", "diagnosis", "procedure", "prior", "authorization"),
            ),
            KnowledgeSnippet(
                domain="prior_authorization",
                source="payer-rules/medical-review",
                excerpt="High-acuity services such as surgery, oncology, and inpatient care often need medical review.",
                keywords=("surgery", "oncology", "inpatient", "medical", "review"),
            ),
        ]

    def search(self, domain: AgentType, query: str, limit: int = 2) -> list[RetrievedContext]:
        tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked: list[RetrievedContext] = []

        for snippet in self.corpus:
            if snippet.domain != domain:
                continue
            overlap = len(tokens.intersection(snippet.keywords))
            if overlap == 0:
                continue
            relevance = min(0.55 + (0.12 * overlap), 0.98)
            ranked.append(
                RetrievedContext(
                    source=snippet.source,
                    excerpt=snippet.excerpt,
                    relevance=round(relevance, 2),
                )
            )

        if not ranked:
            fallback = [
                RetrievedContext(
                    source=snippet.source,
                    excerpt=snippet.excerpt,
                    relevance=0.5,
                )
                for snippet in self.corpus
                if snippet.domain == domain
            ]
            return fallback[:limit]

        ranked.sort(key=lambda item: item.relevance, reverse=True)
        return ranked[:limit]
