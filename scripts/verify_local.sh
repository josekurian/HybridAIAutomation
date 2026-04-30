#!/bin/bash

set -euo pipefail

python3 -m pytest -q

(
  cd frontend
  npm run build
)

docker compose config
