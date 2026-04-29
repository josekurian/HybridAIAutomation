import { FormEvent, useDeferredValue, useState, useTransition } from "react";

type AgentType = "invoice" | "prior_authorization";
type ProviderType = "local" | "openai" | "oci";

type AgentResponse = {
  agent_type: AgentType;
  provider: ProviderType;
  status: string;
  summary: string;
  extracted_fields: Record<string, string | null>;
  next_actions: string[];
  routing_target: string;
  confidence: number;
  retrieved_context: Array<{
    source: string;
    excerpt: string;
    relevance: number;
  }>;
  processing_notes: string[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

const invoiceSample = `Invoice Number: INV-2026-041
Vendor: Northwind Medical Supplies
Amount Due: 12480.00
Due Date: 2026-05-15
PO Number: PO-88412`;

const priorAuthSample = `Patient: Elena Carter
Member ID: MBR-55291
Payer: Evergreen Health Plan
Diagnosis: Lumbar radiculopathy
Procedure: MRI lumbar spine
Ordering Provider: Dr. Ravi Patel`;

export default function App() {
  const [agentType, setAgentType] = useState<AgentType>("invoice");
  const [provider, setProvider] = useState<ProviderType>("local");
  const [documentText, setDocumentText] = useState(invoiceSample);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const deferredDocumentText = useDeferredValue(documentText);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_type: agentType,
          provider,
          document_text: documentText,
          use_retrieval: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }

      const payload = (await response.json()) as AgentResponse;
      startTransition(() => setResult(payload));
    } catch (submitError) {
      setResult(null);
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unknown request failure.",
      );
    }
  }

  function loadSample(nextAgent: AgentType) {
    setAgentType(nextAgent);
    setResult(null);
    setError(null);
    setDocumentText(nextAgent === "invoice" ? invoiceSample : priorAuthSample);
  }

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Hybrid operations cockpit</p>
          <h1>Document workflows with deterministic routing and optional AI enrichment.</h1>
          <p className="hero-copy">
            Start local, plug in OpenAI or OCI later, and keep a clear path to
            finance and healthcare automation use cases.
          </p>
        </div>
        <div className="hero-metrics">
          <Metric label="Agents" value="2 live flows" />
          <Metric label="Fallback mode" value="Always local-ready" />
          <Metric label="Delivery target" value="API + UI + infra" />
        </div>
      </header>

      <main className="workspace">
        <section className="panel input-panel">
          <div className="panel-header">
            <h2>Run an agent</h2>
            <div className="actions">
              <button type="button" onClick={() => loadSample("invoice")}>
                Load invoice
              </button>
              <button type="button" onClick={() => loadSample("prior_authorization")}>
                Load prior auth
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="form-grid">
            <label>
              Agent
              <select
                value={agentType}
                onChange={(event) => setAgentType(event.target.value as AgentType)}
              >
                <option value="invoice">Invoice</option>
                <option value="prior_authorization">Prior Authorization</option>
              </select>
            </label>

            <label>
              Provider
              <select
                value={provider}
                onChange={(event) => setProvider(event.target.value as ProviderType)}
              >
                <option value="local">Local deterministic</option>
                <option value="openai">OpenAI summary</option>
                <option value="oci">OCI summary</option>
              </select>
            </label>

            <label className="full-width">
              Document text
              <textarea
                rows={12}
                value={documentText}
                onChange={(event) => setDocumentText(event.target.value)}
              />
            </label>

            <div className="submit-row full-width">
              <span className="helper-text">
                {deferredDocumentText.length} characters of source text
              </span>
              <button type="submit" className="submit-button" disabled={isPending}>
                {isPending ? "Running..." : "Run workflow"}
              </button>
            </div>
          </form>
        </section>

        <section className="panel output-panel">
          <div className="panel-header">
            <h2>Workflow result</h2>
            <span className="status-pill">
              {result ? `${result.status} via ${result.provider}` : "Waiting for input"}
            </span>
          </div>

          {error ? <div className="error-box">{error}</div> : null}

          {result ? (
            <div className="result-grid">
              <article className="result-card accent-card">
                <p className="label">Summary</p>
                <p className="summary">{result.summary}</p>
                <div className="meta-row">
                  <span>Route: {result.routing_target}</span>
                  <span>Confidence: {result.confidence}</span>
                </div>
              </article>

              <article className="result-card">
                <p className="label">Extracted fields</p>
                <dl className="fields">
                  {Object.entries(result.extracted_fields).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key.replace(/_/g, " ")}</dt>
                      <dd>{value || "Not found"}</dd>
                    </div>
                  ))}
                </dl>
              </article>

              <article className="result-card">
                <p className="label">Next actions</p>
                <ul className="list">
                  {result.next_actions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Retrieved context</p>
                <ul className="list">
                  {result.retrieved_context.map((item) => (
                    <li key={`${item.source}-${item.excerpt}`}>
                      <strong>{item.source}</strong>: {item.excerpt}
                    </li>
                  ))}
                </ul>
              </article>

              {result.processing_notes.length > 0 ? (
                <article className="result-card">
                  <p className="label">Processing notes</p>
                  <ul className="list">
                    {result.processing_notes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ) : null}
            </div>
          ) : (
            <div className="empty-state">
              <p>Run one of the sample documents to see extracted fields, route selection, and follow-up actions.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
