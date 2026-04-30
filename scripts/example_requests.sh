#!/bin/bash

set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:5405}"

curl -sS "$API_BASE_URL/health"
echo

curl -sS \
  -X POST "$API_BASE_URL/api/v1/workflows/invoice_processing/run" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "local",
    "document_text": "Invoice Number: INV-2026-041 Vendor: Northwind Medical Supplies Amount Due: 12480.00 Due Date: 2026-05-15 PO Number: PO-88412"
  }'
echo
