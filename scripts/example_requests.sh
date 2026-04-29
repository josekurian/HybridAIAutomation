#!/bin/bash

set -euo pipefail

curl -sS http://localhost:8000/health
echo

curl -sS \
  -X POST http://localhost:8000/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "invoice",
    "provider": "local",
    "document_text": "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
  }'
echo
