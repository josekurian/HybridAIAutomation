#!/bin/bash

set -euo pipefail

echo "Creating HybridAIAutomation structure..."

directories=(
  "frontend/src"
  "backend/app/api/routes"
  "backend/app/agents"
  "backend/app/ai"
  "backend/app/orchestration"
  "backend/app/rag"
  "backend/app/integrations"
  "backend/app/db"
  "backend/app/core"
  "infrastructure/terraform/oci"
  "infrastructure/kubernetes"
  "workflows"
  "docs"
  "tests"
  "scripts"
)

files=(
  "README.md"
  ".env.example"
  ".gitignore"
  "docker-compose.yml"
  "backend/Dockerfile"
  "backend/requirements.txt"
  "backend/app/main.py"
  "backend/app/api/routes/agents.py"
  "backend/app/orchestration/agent_router.py"
  "backend/app/agents/invoice_agent.py"
  "backend/app/agents/prior_auth_agent.py"
  "backend/app/ai/openai_client.py"
  "backend/app/ai/oci_ai_client.py"
  "backend/app/rag/retrieval.py"
  "frontend/Dockerfile"
  "frontend/index.html"
  "frontend/package.json"
  "frontend/src/App.tsx"
  "infrastructure/terraform/oci/main.tf"
  "infrastructure/kubernetes/deployment.yaml"
  "workflows/invoice_processing.yaml"
  "workflows/prior_authorization.yaml"
)

for dir in "${directories[@]}"; do
  mkdir -p "$dir"
done

for file in "${files[@]}"; do
  mkdir -p "$(dirname "$file")"
  touch "$file"
done

echo "Project structure created."
