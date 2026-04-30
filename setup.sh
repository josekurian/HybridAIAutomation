#!/bin/bash

set -euo pipefail

echo "Creating HybridAIAutomation structure..."

directories=(
  ".github/workflows"
  "data"
  "frontend/src"
  "backend/app/api/routes"
  "backend/app/agents"
  "backend/app/ai"
  "backend/app/audit"
  "backend/app/orchestration"
  "backend/app/rag"
  "backend/app/integrations"
  "backend/app/db"
  "backend/app/core"
  "backend/app/workflows"
  "infrastructure/terraform/oci"
  "infrastructure/kubernetes"
  "workflows"
  "docs"
  "docs/phases"
  "docs/workflows"
  "tests"
  "scripts"
)

files=(
  "README.md"
  "Makefile"
  ".env.example"
  ".gitignore"
  ".dockerignore"
  "docker-compose.yml"
  "backend/Dockerfile"
  "backend/requirements.txt"
  "backend/app/main.py"
  "backend/app/api/routes/agents.py"
  "backend/app/api/routes/auth.py"
  "backend/app/api/routes/audit.py"
  "backend/app/api/routes/workflows.py"
  "backend/app/core/security.py"
  "backend/app/orchestration/agent_router.py"
  "backend/app/audit/service.py"
  "backend/app/agents/invoice_agent.py"
  "backend/app/agents/prior_auth_agent.py"
  "backend/app/ai/openai_client.py"
  "backend/app/ai/oci_ai_client.py"
  "backend/app/integrations/oracle_erp.py"
  "backend/app/integrations/oracle_health.py"
  "backend/app/rag/retrieval.py"
  "backend/app/workflows/registry.py"
  "backend/app/workflows/service.py"
  "frontend/Dockerfile"
  "frontend/.dockerignore"
  "frontend/index.html"
  "frontend/package.json"
  "frontend/src/App.tsx"
  "infrastructure/terraform/oci/main.tf"
  "infrastructure/kubernetes/deployment.yaml"
  ".github/workflows/ci.yml"
  "docs/README.md"
  "docs/architecture.md"
  "docs/repository-structure.md"
  "scripts/verify_local.sh"
  "workflows/invoice_processing.yaml"
  "workflows/prior_authorization.yaml"
  "tests/conftest.py"
)

for dir in "${directories[@]}"; do
  mkdir -p "$dir"
done

for file in "${files[@]}"; do
  mkdir -p "$(dirname "$file")"
  touch "$file"
done

echo "Project structure created."
