PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
NPM ?= npm

.PHONY: backend-install frontend-install test frontend-build compose-config docker-build verify export-docs

backend-install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && $(PIP) install -r backend/requirements.txt

frontend-install:
	cd frontend && $(NPM) ci

test:
	$(PYTHON) -m pytest -q

frontend-build:
	cd frontend && $(NPM) run build

compose-config:
	docker compose config

docker-build:
	docker compose build backend frontend

verify: test frontend-build compose-config

export-docs:
	$(PYTHON) scripts/export_markdown_artifacts.py
