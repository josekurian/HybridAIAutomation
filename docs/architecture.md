# Architecture Overview

## Backend

- `backend/app/main.py` exposes the FastAPI service.
- `backend/app/api/routes/agents.py` provides the public agent endpoints.
- `backend/app/orchestration/agent_router.py` coordinates retrieval, local logic,
  and optional AI summarization.
- `backend/app/agents/` contains workflow-specific extraction logic.
- `backend/app/rag/retrieval.py` provides a lightweight in-memory knowledge base.

## Frontend

- `frontend/src/App.tsx` is a single-screen operator console for sample runs.
- The UI submits document text, displays extracted fields, and surfaces route
  recommendations and fallback notes.

## Deployment assets

- `docker-compose.yml` starts the API and frontend locally.
- `infrastructure/terraform/oci/main.tf` is a provider-ready OCI starter.
- `infrastructure/kubernetes/deployment.yaml` contains baseline deployments and services.

## Intended extension points

- Replace regex extraction with OCR and structured document parsers.
- Swap the in-memory retrieval layer for a vector index or enterprise knowledge base.
- Add persistence for workflow runs, approvals, and audit logs.
- Connect OCI AI to your tenancy-specific request schema and auth model.
