# DOCUPRO developer tasks. All commands run from the repository's docupro/ folder.
SHELL := /bin/bash
API := services/api
WEB := apps/web
PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: help setup setup-ocr api web dev lint fmt test verify docker run clean

help:
	@echo "make setup   create .venv and install backend + web dependencies"
	@echo "make setup-ocr  same, plus the pip-only OCR fallback (RapidOCR)"
	@echo "make api     run the API on :8000 (with hot reload)"
	@echo "make web     run the Vite dev server on :5173"
	@echo "make dev     run API and web together"
	@echo "make test    backend tests + web typecheck + production build"
	@echo "make lint    ruff check/format --check and tsc --noEmit"
	@echo "make verify  run every advertised conversion against the corpus"
	@echo "make docker  build the production image"
	@echo "make run     build the web client and serve everything on :8000"

setup:
	./scripts/setup_env.sh
	cd $(WEB) && npm ci

setup-ocr:
	./scripts/setup_env.sh --ocr
	cd $(WEB) && npm ci

api:
	cd $(API) && ../../$(PY) -m uvicorn docupro_api.main:app --reload --port 8000

web:
	cd $(WEB) && npm run dev

dev:
	@trap 'kill 0' INT; (cd $(API) && ../../$(PY) -m uvicorn docupro_api.main:app --reload --port 8000) & (cd $(WEB) && npm run dev) & wait

lint:
	cd $(API) && ../../$(PY) -m ruff check . && ../../$(PY) -m ruff format --check .
	cd $(WEB) && npx tsc --noEmit

fmt:
	cd $(API) && ../../$(PY) -m ruff check --fix . && ../../$(PY) -m ruff format .

test:
	cd $(API) && ../../$(PY) -m pytest -q
	cd $(WEB) && npx tsc --noEmit && npm run build

verify:
	cd $(API) && ../../$(PY) ../../scripts/verify_engines.py --corpus ../../tests/corpus/generated

docker:
	docker build -t docupro:1.0.0 .

run:
	cd $(WEB) && npm run build
	DOCUPRO_WEB_DIR=$(CURDIR)/$(WEB)/dist $(PY) -m uvicorn docupro_api.main:app --app-dir $(API) --host 0.0.0.0 --port 8000

clean:
	rm -rf $(WEB)/dist $(API)/.pytest_cache $(API)/.ruff_cache
	find $(API) -name __pycache__ -type d -prune -exec rm -rf {} +
