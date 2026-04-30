import { FormEvent, useDeferredValue, useEffect, useState, useTransition } from "react";

type AgentType = "invoice" | "prior_authorization";
type ProviderType = "local" | "openai" | "oci";
type WorkflowName = "invoice_processing" | "prior_authorization";

type WorkflowStep = {
  id: string;
  action: string;
  status: "completed" | "skipped" | "flagged";
  detail: string;
};

type TeamMember = {
  agent_id: string;
  name: string;
  role: string;
  status: string;
  notes: string[];
};

type TeamHandoff = {
  from_agent: string;
  to_agent: string;
  reason: string;
  status: string;
};

type SpecialistFinding = {
  agent_id: string;
  title: string;
  detail: string;
  severity: "info" | "warning" | "critical";
};

type MultiAgentExecution = {
  team_id: string;
  team_name: string;
  orchestration_mode: string;
  members: TeamMember[];
  handoffs: TeamHandoff[];
  findings: SpecialistFinding[];
};

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
  decision_trace: Array<{
    step: string;
    detail: string;
  }>;
  integration_results: Array<{
    system: string;
    action: string;
    status: string;
    reference: string | null;
    details: Record<string, unknown>;
  }>;
  processing_notes: string[];
  audit_event_id: string | null;
  orchestration: MultiAgentExecution | null;
  estimated_input_tokens: number | null;
  estimated_output_tokens: number | null;
};

type WorkflowResponse = {
  workflow_name: WorkflowName;
  workflow_version: number;
  status: string;
  steps: WorkflowStep[];
  agent_result: AgentResponse;
};

type AgentTemplate = {
  template_id: string;
  name: string;
  domain: "finance" | "healthcare";
  mapped_agent_type: AgentType;
  summary: string;
  orchestration_mode: string;
  data_sources: string[];
  tools: string[];
  tags: string[];
};

type SampleUseCase = {
  use_case_id: string;
  title: string;
  domain: "finance" | "healthcare";
  template_id: string;
  workflow_name: WorkflowName;
  provider: ProviderType;
  expected_route: string;
  sample_document_text: string;
  enabled_capabilities: string[];
  outcome_summary: string;
};

type CredentialRecord = {
  alias: string;
  scope: string;
  integrations: string[];
  masked_value: string;
  created_at: string;
};

type MonitoringSnapshot = {
  generated_at: string;
  total_runs: number;
  success_rate: number;
  average_latency_ms: number;
  error_rate: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  runs_by_workflow: Record<string, number>;
  runs_by_provider: Record<string, number>;
  recent_events: Array<Record<string, string | number>>;
};

type RestIntegration = {
  integration_id: string;
  name: string;
  domain: "finance" | "healthcare" | "shared";
  method: "GET" | "POST" | "PATCH";
  path: string;
  privilege_hint: string;
  required_credential_scope: string;
  sample_payload: Record<string, unknown>;
  mapped_use_case_ids: string[];
};

type MarketplaceItem = {
  item_id: string;
  name: string;
  publisher: string;
  domain: "finance" | "healthcare" | "shared";
  summary: string;
  capabilities: string[];
  template_id: string;
  validated_for: string[];
};

type BuilderNode = {
  node_id: string;
  title: string;
  kind: string;
  depends_on: string[];
  configuration: Record<string, unknown>;
};

type BuilderResponse = {
  blueprint_id: string;
  template_id: string;
  workflow_name: string;
  display_name: string;
  provider: ProviderType;
  orchestration_mode: string;
  nodes: BuilderNode[];
  credential_aliases: string[];
  enabled_tools: string[];
  sample_payload: Record<string, unknown>;
};

type ValidationReport = {
  blueprint_id: string | null;
  overall_status: string;
  checks: Array<{
    name: string;
    status: string;
    detail: string;
  }>;
  scenario_results: Array<{
    use_case_id: string;
    workflow_name: WorkflowName;
    status: string;
    expected_route: string;
    actual_route: string;
    summary: string;
  }>;
};

type RestSimulationResponse = {
  integration_id: string;
  status: string;
  reference: string;
  endpoint: string;
  request_preview: Record<string, unknown>;
  notes: string[];
};

type MarketplaceInstallResponse = {
  item_id: string;
  blueprint: BuilderResponse;
  notes: string[];
};

type StudioOverview = {
  templates: AgentTemplate[];
  sample_use_cases: SampleUseCase[];
  credentials: CredentialRecord[];
  monitoring: MonitoringSnapshot;
  integrations: RestIntegration[];
  marketplace_items: MarketplaceItem[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:5405";

const workflowByAgent: Record<AgentType, WorkflowName> = {
  invoice: "invoice_processing",
  prior_authorization: "prior_authorization",
};

const defaultSamples: Record<AgentType, string> = {
  invoice:
    "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412",
  prior_authorization:
    "Patient: Elena Carter Member ID: MBR-55291 Payer: Evergreen Health Plan Diagnosis: Lumbar radiculopathy Procedure: MRI lumbar spine Ordering Provider: Dr. Ravi Patel",
};

export default function App() {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [agentType, setAgentType] = useState<AgentType>("invoice");
  const [provider, setProvider] = useState<ProviderType>("local");
  const [documentText, setDocumentText] = useState(defaultSamples.invoice);
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowResponse | null>(null);
  const [overview, setOverview] = useState<StudioOverview | null>(null);
  const [blueprint, setBlueprint] = useState<BuilderResponse | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [integrationPreview, setIntegrationPreview] = useState<RestSimulationResponse | null>(null);
  const [marketplaceInstall, setMarketplaceInstall] = useState<MarketplaceInstallResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [studioError, setStudioError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [credentialAlias, setCredentialAlias] = useState("oracle-erp-demo");
  const [credentialSecret, setCredentialSecret] = useState("demo-secret-token");
  const [credentialScope, setCredentialScope] = useState("oracle_erp");
  const [isPending, startTransition] = useTransition();
  const [isStudioPending, startStudioTransition] = useTransition();
  const deferredDocumentText = useDeferredValue(documentText);

  useEffect(() => {
    void bootstrapSession();
  }, []);

  async function bootstrapSession() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "demo-admin",
          password: "demo-password",
        }),
      });
      if (!response.ok) {
        throw new Error(`Token request failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as { access_token: string };
      setAuthToken(payload.access_token);
      await refreshOverview(payload.access_token);
    } catch (tokenError) {
      setStudioError(
        tokenError instanceof Error ? tokenError.message : "Failed to initialize demo token.",
      );
    }
  }

  async function authorizedFetch(
    input: string,
    init: RequestInit = {},
    overrideToken?: string,
  ) {
    const token = overrideToken || authToken;
    const headers = new Headers(init.headers || {});
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return fetch(input, { ...init, headers });
  }

  async function refreshOverview(overrideToken?: string) {
    try {
      const response = await authorizedFetch(
        `${API_BASE_URL}/api/v1/studio/overview`,
        {},
        overrideToken,
      );
      if (!response.ok) {
        throw new Error(`Overview request failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as StudioOverview;
      setOverview(payload);
      setStudioError(null);
    } catch (overviewError) {
      setStudioError(
        overviewError instanceof Error ? overviewError.message : "Failed to load studio overview.",
      );
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      const workflowName = workflowByAgent[agentType];
      const response = await authorizedFetch(
        `${API_BASE_URL}/api/v1/workflows/${workflowName}/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider,
            document_text: documentText,
            use_retrieval: true,
            metadata: { selected_use_case_id: selectedUseCaseId },
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }

      const payload = (await response.json()) as WorkflowResponse;
      startTransition(() => setResult(payload));
      void refreshOverview();
    } catch (submitError) {
      setResult(null);
      setError(
        submitError instanceof Error ? submitError.message : "Unknown request failure.",
      );
    }
  }

  function loadSample(nextAgent: AgentType) {
    setAgentType(nextAgent);
    setProvider("local");
    setSelectedUseCaseId(null);
    setResult(null);
    setError(null);
    setDocumentText(defaultSamples[nextAgent]);
  }

  function applyUseCase(useCase: SampleUseCase) {
    setSelectedUseCaseId(useCase.use_case_id);
    setAgentType(
      useCase.workflow_name === "invoice_processing" ? "invoice" : "prior_authorization",
    );
    setProvider(useCase.provider);
    setDocumentText(useCase.sample_document_text);
    setActionMessage(`Loaded sample use case: ${useCase.title}`);
  }

  function buildBuilderRequest(templateId: string) {
    return {
      template_id: templateId,
      workflow_name: workflowByAgent[agentType],
      display_name: selectedUseCaseId
        ? `${selectedUseCaseId}-blueprint`
        : `${workflowByAgent[agentType]}-blueprint`,
      provider,
      enabled_tools: [],
      data_sources: [],
      credential_aliases: credentialScope ? [credentialAlias] : [],
      custom_instructions: selectedUseCaseId
        ? `Prepared from sample use case ${selectedUseCaseId}.`
        : "Prepared from the operator console.",
      thresholds: agentType === "invoice" ? { high_value_amount: 10000 } : { medical_review_score: 0.8 },
    };
  }

  async function composeBlueprint(templateId: string) {
    setStudioError(null);
    setActionMessage(null);
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/api/v1/studio/builders/compose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildBuilderRequest(templateId)),
      });
      if (!response.ok) {
        throw new Error(`Blueprint compose failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as BuilderResponse;
      startStudioTransition(() => setBlueprint(payload));
      setActionMessage(`Composed blueprint ${payload.blueprint_id}.`);
    } catch (composeError) {
      setStudioError(
        composeError instanceof Error ? composeError.message : "Failed to compose blueprint.",
      );
    }
  }

  async function validateBlueprint(templateId: string) {
    setStudioError(null);
    setActionMessage(null);
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/api/v1/studio/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildBuilderRequest(templateId)),
      });
      if (!response.ok) {
        throw new Error(`Validation failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as ValidationReport;
      startStudioTransition(() => setValidation(payload));
      void refreshOverview();
      setActionMessage(`Validation completed with status ${payload.overall_status}.`);
    } catch (validationError) {
      setStudioError(
        validationError instanceof Error ? validationError.message : "Failed to validate blueprint.",
      );
    }
  }

  async function saveCredential(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStudioError(null);
    setActionMessage(null);
    try {
      const response = await authorizedFetch(`${API_BASE_URL}/api/v1/studio/credentials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alias: credentialAlias,
          secret_value: credentialSecret,
          scope: credentialScope,
          integrations: overview?.integrations
            .filter((item) => item.required_credential_scope === credentialScope)
            .map((item) => item.integration_id) || [],
        }),
      });
      if (!response.ok) {
        throw new Error(`Credential save failed with status ${response.status}.`);
      }
      await refreshOverview();
      setActionMessage(`Stored demo credential alias ${credentialAlias}.`);
    } catch (credentialError) {
      setStudioError(
        credentialError instanceof Error ? credentialError.message : "Failed to save credential.",
      );
    }
  }

  async function simulateIntegration(integrationId: string) {
    setStudioError(null);
    setActionMessage(null);
    try {
      const integration = overview?.integrations.find((item) => item.integration_id === integrationId);
      const response = await authorizedFetch(`${API_BASE_URL}/api/v1/studio/integrations/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          integration_id: integrationId,
          credential_alias: integration?.required_credential_scope === credentialScope ? credentialAlias : null,
          payload: integration?.sample_payload || {},
        }),
      });
      if (!response.ok) {
        throw new Error(`Integration simulation failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as RestSimulationResponse;
      startStudioTransition(() => setIntegrationPreview(payload));
      setActionMessage(`Simulated integration ${payload.integration_id}.`);
    } catch (integrationError) {
      setStudioError(
        integrationError instanceof Error ? integrationError.message : "Failed to simulate integration.",
      );
    }
  }

  async function installMarketplace(itemId: string) {
    setStudioError(null);
    setActionMessage(null);
    try {
      const response = await authorizedFetch(
        `${API_BASE_URL}/api/v1/studio/marketplace/items/${itemId}/install`,
        {
          method: "POST",
        },
      );
      if (!response.ok) {
        throw new Error(`Marketplace install failed with status ${response.status}.`);
      }
      const payload = (await response.json()) as MarketplaceInstallResponse;
      startStudioTransition(() => setMarketplaceInstall(payload));
      setActionMessage(`Installed marketplace pack ${payload.item_id}.`);
    } catch (installError) {
      setStudioError(
        installError instanceof Error ? installError.message : "Failed to install marketplace item.",
      );
    }
  }

  const agentResult = result?.agent_result ?? null;
  const activeTemplates =
    overview?.templates.filter((template) => template.mapped_agent_type === agentType) || [];
  const activeUseCases =
    overview?.sample_use_cases.filter(
      (useCase) => useCase.workflow_name === workflowByAgent[agentType],
    ) || [];

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Enterprise workflow cockpit</p>
          <h1>Expand invoice and prior-auth POCs into a usable AI automation studio.</h1>
          <p className="hero-copy">
            Run production-oriented sample workflows, compose low-code blueprints,
            inspect multi-agent handoffs, manage demo credentials, validate scenarios,
            preview REST integrations, and install marketplace packs from one surface.
          </p>
        </div>
        <div className="hero-metrics">
          <Metric label="Capability set" value="Templates, builder, orchestration" />
          <Metric label="Runtime view" value="Validation, monitoring, REST previews" />
          <Metric label="Target domains" value="Oracle AP + Prior Auth" />
        </div>
      </header>

      <main className="workspace">
        <section className="panel input-panel">
          <div className="panel-header">
            <h2>Run workflow</h2>
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
              Workflow
              <select
                value={agentType}
                onChange={(event) => setAgentType(event.target.value as AgentType)}
              >
                <option value="invoice">Invoice Processing</option>
                <option value="prior_authorization">Prior Authorization</option>
              </select>
            </label>

            <label>
              Enrichment provider
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

          <div className="stack-section">
            <div className="subheader">
              <h3>Sample use cases</h3>
              <span>{activeUseCases.length} ready-made scenarios</span>
            </div>
            <div className="chip-grid">
              {activeUseCases.map((useCase) => (
                <button
                  key={useCase.use_case_id}
                  type="button"
                  className="chip-card"
                  onClick={() => applyUseCase(useCase)}
                >
                  <strong>{useCase.title}</strong>
                  <span>{useCase.expected_route}</span>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="panel output-panel">
          <div className="panel-header">
            <h2>POC output</h2>
            <span className="status-pill">
              {result ? `${result.status} / ${result.workflow_name}` : "Waiting for execution"}
            </span>
          </div>

          {error ? <div className="error-box">{error}</div> : null}
          {studioError ? <div className="error-box">{studioError}</div> : null}
          {actionMessage ? <div className="info-box">{actionMessage}</div> : null}

          {result && agentResult ? (
            <div className="result-grid">
              <article className="result-card accent-card">
                <p className="label">Executive summary</p>
                <p className="summary">{agentResult.summary}</p>
                <div className="meta-row">
                  <span>Route: {agentResult.routing_target}</span>
                  <span>Confidence: {agentResult.confidence}</span>
                  <span>Audit ID: {agentResult.audit_event_id || "pending"}</span>
                  <span>
                    Tokens: {agentResult.estimated_input_tokens || 0} in /{" "}
                    {agentResult.estimated_output_tokens || 0} out
                  </span>
                </div>
              </article>

              <article className="result-card">
                <p className="label">Workflow steps</p>
                <ul className="list">
                  {result.steps.map((step) => (
                    <li key={step.id}>
                      <strong>{step.id}</strong> ({step.status}): {step.detail}
                    </li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Multi-agent orchestration</p>
                {agentResult.orchestration ? (
                  <div className="stacked-grid">
                    <p className="inline-meta">
                      {agentResult.orchestration.team_name} /{" "}
                      {agentResult.orchestration.orchestration_mode}
                    </p>
                    <ul className="list">
                      {agentResult.orchestration.members.map((member) => (
                        <li key={member.agent_id}>
                          <strong>{member.name}</strong> ({member.status}): {member.role}
                        </li>
                      ))}
                    </ul>
                    <ul className="list">
                      {agentResult.orchestration.handoffs.map((handoff) => (
                        <li key={`${handoff.from_agent}-${handoff.to_agent}`}>
                          <strong>{handoff.from_agent}</strong> to <strong>{handoff.to_agent}</strong>
                          : {handoff.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p>No orchestration data returned.</p>
                )}
              </article>

              <article className="result-card">
                <p className="label">Specialist findings</p>
                <ul className="list">
                  {(agentResult.orchestration?.findings || []).map((item) => (
                    <li key={`${item.agent_id}-${item.title}`}>
                      <strong>{item.title}</strong> [{item.severity}]: {item.detail}
                    </li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Extracted fields</p>
                <dl className="fields">
                  {Object.entries(agentResult.extracted_fields).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key.replace(/_/g, " ")}</dt>
                      <dd>{value || "Not found"}</dd>
                    </div>
                  ))}
                </dl>
              </article>

              <article className="result-card">
                <p className="label">Decision trace</p>
                <ul className="list">
                  {agentResult.decision_trace.map((item) => (
                    <li key={`${item.step}-${item.detail}`}>
                      <strong>{item.step}</strong>: {item.detail}
                    </li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Oracle integration handoff</p>
                <ul className="list">
                  {agentResult.integration_results.map((item) => (
                    <li key={`${item.system}-${item.action}-${item.reference || "none"}`}>
                      <strong>{item.system}</strong> / {item.action} ({item.status})
                      {item.reference ? ` - ${item.reference}` : ""}
                      <pre className="json-block">
                        {JSON.stringify(item.details, null, 2)}
                      </pre>
                    </li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Next actions</p>
                <ul className="list">
                  {agentResult.next_actions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <p className="label">Retrieved context</p>
                <ul className="list">
                  {agentResult.retrieved_context.map((item) => (
                    <li key={`${item.source}-${item.excerpt}`}>
                      <strong>{item.source}</strong>: {item.excerpt}
                    </li>
                  ))}
                </ul>
              </article>

              {agentResult.processing_notes.length > 0 ? (
                <article className="result-card">
                  <p className="label">Processing notes</p>
                  <ul className="list">
                    {agentResult.processing_notes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ) : null}
            </div>
          ) : (
            <div className="empty-state">
              <p>
                Run one of the POC workflows to see step-by-step execution,
                multi-agent handoffs, Oracle handoff stubs, validation-ready outputs,
                and monitoring metadata.
              </p>
            </div>
          )}
        </section>
      </main>

      <section className="platform-grid">
        <article className="panel">
          <div className="subheader">
            <h3>Agent template library</h3>
            <span>Natural-language starter templates</span>
          </div>
          <div className="template-grid">
            {activeTemplates.map((template) => (
              <div className="template-card" key={template.template_id}>
                <strong>{template.name}</strong>
                <p>{template.summary}</p>
                <div className="mini-meta">
                  <span>{template.orchestration_mode}</span>
                  <span>{template.tools.length} tools</span>
                </div>
                <div className="chip-row">
                  {template.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="inline-actions">
                  <button type="button" onClick={() => composeBlueprint(template.template_id)}>
                    Compose blueprint
                  </button>
                  <button type="button" onClick={() => validateBlueprint(template.template_id)}>
                    Validate
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>No-code / low-code builder</h3>
            <span>Composed workflow graph</span>
          </div>
          {blueprint ? (
            <div className="stacked-grid">
              <p className="inline-meta">
                {blueprint.display_name} / {blueprint.blueprint_id}
              </p>
              <ul className="list">
                {blueprint.nodes.map((node) => (
                  <li key={node.node_id}>
                    <strong>{node.title}</strong> ({node.kind}) depends on{" "}
                    {node.depends_on.length > 0 ? node.depends_on.join(", ") : "nothing"}
                  </li>
                ))}
              </ul>
              <pre className="json-block">{JSON.stringify(blueprint.sample_payload, null, 2)}</pre>
            </div>
          ) : (
            <p className="empty-text">
              Compose a blueprint from one of the active templates to preview the low-code graph.
            </p>
          )}
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>Validation and testing</h3>
            <span>Scenario checks against real sample runs</span>
          </div>
          {validation ? (
            <div className="stacked-grid">
              <p className="inline-meta">Overall status: {validation.overall_status}</p>
              <ul className="list">
                {validation.checks.map((check) => (
                  <li key={check.name}>
                    <strong>{check.name}</strong> ({check.status}): {check.detail}
                  </li>
                ))}
              </ul>
              <ul className="list">
                {validation.scenario_results.map((scenario) => (
                  <li key={scenario.use_case_id}>
                    <strong>{scenario.use_case_id}</strong> ({scenario.status}): expected{" "}
                    {scenario.expected_route}, actual {scenario.actual_route}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="empty-text">
              Run validation from a template card to execute packaged scenario checks.
            </p>
          )}
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>Credential store</h3>
            <span>Demo vault for REST and agent actions</span>
          </div>
          <form className="credential-form" onSubmit={saveCredential}>
            <input
              value={credentialAlias}
              onChange={(event) => setCredentialAlias(event.target.value)}
              placeholder="alias"
            />
            <input
              value={credentialScope}
              onChange={(event) => setCredentialScope(event.target.value)}
              placeholder="scope"
            />
            <input
              value={credentialSecret}
              onChange={(event) => setCredentialSecret(event.target.value)}
              placeholder="secret"
            />
            <button type="submit">Save credential</button>
          </form>
          <ul className="list compact-list">
            {(overview?.credentials || []).map((credential) => (
              <li key={credential.alias}>
                <strong>{credential.alias}</strong> [{credential.scope}] {credential.masked_value}
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>REST API integration</h3>
            <span>Oracle ERP and Oracle Health handoff simulations</span>
          </div>
          <div className="template-grid">
            {(overview?.integrations || []).map((integration) => (
              <div key={integration.integration_id} className="template-card">
                <strong>{integration.name}</strong>
                <p>
                  {integration.method} {integration.path}
                </p>
                <div className="mini-meta">
                  <span>{integration.domain}</span>
                  <span>{integration.required_credential_scope}</span>
                </div>
                <button type="button" onClick={() => simulateIntegration(integration.integration_id)}>
                  Simulate call
                </button>
              </div>
            ))}
          </div>
          {integrationPreview ? (
            <pre className="json-block">{JSON.stringify(integrationPreview, null, 2)}</pre>
          ) : null}
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>Monitoring dashboard</h3>
            <span>Real-time demo metrics</span>
          </div>
          {overview?.monitoring ? (
            <div className="stacked-grid">
              <div className="monitor-grid">
                <Metric label="Runs" value={String(overview.monitoring.total_runs)} />
                <Metric label="Success rate" value={`${overview.monitoring.success_rate}`} />
                <Metric label="Latency ms" value={`${overview.monitoring.average_latency_ms}`} />
              </div>
              <ul className="list compact-list">
                {overview.monitoring.recent_events.map((event, index) => (
                  <li key={`${event.workflow_name}-${index}`}>
                    <strong>{String(event.workflow_name)}</strong> / {String(event.provider)} /{" "}
                    {String(event.latency_ms)} ms / {String(event.routing_target)}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="empty-text">Monitoring data will appear after workflow executions.</p>
          )}
        </article>

        <article className="panel">
          <div className="subheader">
            <h3>AI agent marketplace</h3>
            <span>Validated accelerators</span>
          </div>
          <div className="template-grid">
            {(overview?.marketplace_items || []).map((item) => (
              <div key={item.item_id} className="template-card">
                <strong>{item.name}</strong>
                <p>{item.summary}</p>
                <div className="chip-row">
                  {item.capabilities.map((capability) => (
                    <span key={capability} className="tag">
                      {capability}
                    </span>
                  ))}
                </div>
                <button type="button" onClick={() => installMarketplace(item.item_id)}>
                  Install pack
                </button>
              </div>
            ))}
          </div>
          {marketplaceInstall ? (
            <pre className="json-block">{JSON.stringify(marketplaceInstall, null, 2)}</pre>
          ) : null}
        </article>
      </section>

      {isStudioPending ? <p className="footer-note">Refreshing studio artifacts…</p> : null}
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
