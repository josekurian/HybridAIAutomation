# HybridAIAutomation

HybridAIAutomation is a starter platform for document-heavy workflow automation.
This scaffold includes a FastAPI backend, a React/Vite frontend, infrastructure
stubs for OCI and Kubernetes, workflow definitions, tests, and an idempotent
bootstrap script.

## What is included

- Invoice processing and prior authorization agent flows
- Deterministic extraction logic that works without external AI credentials
- Optional OpenAI Responses API integration for richer summaries
- Optional OCI AI endpoint adapter for tenancy-specific model deployments
- Docker Compose setup for local bring-up
- Terraform and Kubernetes starter manifests for future deployment work

## Project layout

```text
HybridAIAutomation/
├── backend/
├── docs/
├── frontend/
├── infrastructure/
├── scripts/
├── tests/
├── workflows/
├── .env.example
├── docker-compose.yml
└── setup.sh
```

## Quickstart

1. Review and copy environment values:

   ```bash
   cp .env.example .env
   ```

2. Start everything with Docker:

   ```bash
   docker-compose up --build
   ```

3. Open the UI:

   - Frontend: `http://localhost:5173`
   - Backend API docs: `http://localhost:8000/docs`

## Local development without Docker

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Bootstrap script

`setup.sh` recreates the folder tree and placeholder files without overwriting
existing content. The repository already contains the scaffold, so you only need
the script if you want to rebuild the layout elsewhere.

## Next steps

- Wire real OCR and document ingestion
- Connect the OCI adapter to your tenancy-specific Generative AI endpoint
- Replace the in-memory retrieval corpus with a vector store or indexed docs
- Add persistence, auth, and queue-based orchestration
