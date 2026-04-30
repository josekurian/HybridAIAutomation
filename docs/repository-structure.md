# Repository Structure Guide

Version: `0.4.1`
Last updated: `2026-04-30`

This document explains the current `HybridAIAutomation` repository layout and
what each major directory is responsible for.

## Top-level layout

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI service, domain agents, orchestration, auth, audit, workflows |
| `frontend/` | React and Vite operator console |
| `docs/` | architecture, delivery, workflow, and phase-level implementation guides |
| `infrastructure/` | OCI Terraform starter and Kubernetes starter manifests |
| `scripts/` | setup, example requests, and markdown export helpers |
| `tests/` | backend API smoke and integration-style tests |
| `workflows/` | business workflow definitions for invoice and prior authorization |
| `data/` | local runtime data such as audit events and credential storage |

## Backend structure

The backend is organized by responsibility rather than by framework layer only.

| Path | Role |
| --- | --- |
| `backend/app/main.py` | FastAPI app bootstrap, router registration, CORS, health endpoints |
| `backend/app/api/routes/` | HTTP route surface for agents, workflows, auth, audit, protocols, and studio APIs |
| `backend/app/agents/` | business-specific agent logic for invoice and prior authorization flows |
| `backend/app/orchestration/` | request routing and multi-agent team orchestration |
| `backend/app/workflows/` | workflow registry and execution service |
| `backend/app/core/` | configuration, schemas, and security helpers |
| `backend/app/audit/` | audit event persistence and retrieval |
| `backend/app/integrations/` | mocked Oracle ERP and Oracle Health handoff adapters |
| `backend/app/ai/` | optional OpenAI and OCI AI client wrappers |
| `backend/app/protocols/` | MCP and A2A protocol metadata and runtime helpers |
| `backend/app/studio/` | blueprint composition, credential registry, monitoring, and marketplace logic |
| `backend/app/rag/` | deterministic retrieval helpers for domain context |

## Frontend structure

The frontend is intentionally small and starter-oriented.

| Path | Role |
| --- | --- |
| `frontend/src/App.tsx` | main operator console and studio surface |
| `frontend/src/styles.css` | page styling and layout |
| `frontend/src/main.tsx` | React bootstrap |
| `frontend/package.json` | frontend scripts and dependency contract |
| `frontend/Dockerfile` | reproducible frontend container build |

## Infrastructure structure

| Path | Role |
| --- | --- |
| `docker-compose.yml` | local stack with frontend, backend, and pgvector database |
| `backend/Dockerfile` | backend image build |
| `frontend/Dockerfile` | frontend image build |
| `infrastructure/terraform/oci/main.tf` | OCI starter infrastructure contract |
| `infrastructure/kubernetes/deployment.yaml` | Kubernetes and OKE deployment starter |

## Documentation structure

| Path | Role |
| --- | --- |
| `docs/README.md` | documentation index |
| `docs/architecture.md` | architecture overview and runtime path |
| `docs/phases/` | phase-by-phase implementation and deployment notes |
| `docs/workflows/` | business workflow walkthroughs |
| `docs/customer-poc-playbook.md` | customer pilot and expansion guidance |
| `docs/repository-structure.md` | this repository structure guide |

## Development and verification structure

| Path | Role |
| --- | --- |
| `Makefile` | local developer commands for test, build, docker, and doc export |
| `scripts/verify_local.sh` | shell-based verification path for test, frontend build, and Docker config |
| `tests/test_api.py` | API smoke tests for auth, workflow, audit, studio, and protocol routes |
| `tests/conftest.py` | test import bootstrap for stable local and CI execution |
| `.github/workflows/ci.yml` | GitHub Actions pipeline for backend tests, frontend build, and Docker validation |
| `.dockerignore` | root Docker build-context hygiene |
| `frontend/.dockerignore` | frontend build-context hygiene |

## Expected local workflow

1. Run `make test` for backend API verification.
2. Run `make frontend-build` for frontend verification.
3. Run `make compose-config` to validate the container stack contract.
4. Run `make docker-build` when validating image builds.
5. Run `bash scripts/verify_local.sh` when a shell-based verification path is preferred.
6. Run `make export-docs` after updating markdown documentation and when `.html` and `.docx` artifacts are needed.

## Current design intent

This repo is a lightweight demo and POC shell, not yet a full enterprise
platform. It is designed to stay small at the app layer while progressively
reusing richer shared capabilities from the local `AIAgents` portfolio for MCP,
workflow packs, Oracle adapters, and stronger control-plane behavior.
