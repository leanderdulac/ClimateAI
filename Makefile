# ==============================================================================
# ClimateWise / FIMCE - Automation Makefile
# ==============================================================================

SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
NPM := npm

.PHONY: help setup dev test test-backend test-frontend test-all lint typecheck build clean start stop status security

help: ## Exibe a lista de comandos disponíveis
	@echo "ClimateWise Makefile - Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Instala dependências do backend (.venv) e frontend (client)
	@echo "Configurando ambiente..."
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -r server/requirements.txt
	@cd client && $(NPM) install
	@echo "Setup concluído."

test: test-backend test-frontend ## Executa testes rápidos do backend e do frontend

test-backend: ## Executa testes unitários e de integração do backend
	@echo "Executando testes do backend..."
	@./run_tests.sh unit
	@./run_tests.sh integration

test-frontend: ## Executa os testes do cliente React (Vitest)
	@echo "Executando testes do frontend..."
	@cd client && $(NPM) run test:run

test-all: ## Executa a suíte de testes completa (unit, integration, performance)
	@echo "Executando suíte completa de testes..."
	@$(PYTEST) server/tests -q
	@cd client && $(NPM) run test:run

lint: ## Executa linters no backend e frontend
	@echo "Linting frontend..."
	@cd client && $(NPM) run lint

typecheck: ## Executa verificação de tipos TypeScript no frontend
	@echo "Checando tipos TypeScript..."
	@cd client && $(NPM) run type-check

build: ## Executa o build de produção do frontend
	@echo "Construindo frontend para produção..."
	@cd client && $(NPM) run build

start: ## Inicia os serviços da plataforma (backend + frontend)
	@./start_platform.sh

stop: ## Encerra os serviços da plataforma
	@./stop_platform.sh

status: ## Verifica status dos servidores e portas
	@./status_platform.sh

load-test: ## Executa teste de carga headless com Locust
	@echo "Executando teste de carga com Locust..."
	@$(PYTHON) -m locust -f server/tests/performance/locustfile.py --headless --host http://localhost:8000 --users 20 --spawn-rate 5 --run-time 15s

security: ## Executa auditoria de vulnerabilidades em dependências
	@echo "Auditando pacotes frontend..."
	@cd client && $(NPM) audit --audit-level=high
	@echo "Checando dependências Python..."
	@$(PYTHON) -m pip check

clean: ## Limpa caches, arquivos temporários e diretórios de build
	@rm -rf client/dist
	@rm -rf coverage_html .coverage .pytest_cache
	@rm -f test_results.log tests.log .test_db.sqlite*
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Ambiente limpo."
