# Praestara Build Makefile
# Simplified commands for docker-compose operations

# Variables
COMPOSE := docker-compose
BUILD_DIR := build/

# ============================================================================
# Core Commands
# ============================================================================

.PHONY: help
help:
	@echo "Praestara Build Commands"
	@echo ""
	@echo "Core Commands:"
	@echo "  make up              - Start all services (foreground mode)"
	@echo "  make up-detached     - Start all services (detached mode)"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make build           - Build all images"
	@echo "  make logs            - View service logs"
	@echo "  make clean           - Remove containers and images"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev-up          - Start services in development mode"
	@echo "  make dev-shell       - Open shell in backend container"
	@echo "  make dev-db-shell    - Connect to PostgreSQL"
	@echo "  make dev-migrate     - Run database migrations"
	@echo "  make dev-test        - Run backend tests"
	@echo ""
	@echo "Traefik Commands:"
	@echo "  make traefik-up      - Start Traefik production stack"
	@echo "  make traefik-down    - Stop Traefik stack"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  make format          - Format code"
	@echo "  make lint            - Run linter"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make frontend-build  - Build frontend image"
	@echo "  make frontend-dev    - Start frontend dev server"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-shell        - Connect to PostgreSQL"
	@echo "  make db-migrate      - Run database migrations"
	@echo "  make db-init         - Initialize database with initial data"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make clean-all       - Remove everything (containers, images, volumes)"
	@echo "  make prune           - Prune unused Docker resources"
	@echo ""

.PHONY: up
up:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env up

.PHONY: up-detached
up-detached:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env up -d

.PHONY: down
down:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env down

.PHONY: restart
restart:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env restart

.PHONY: build
build:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env build

.PHONY: logs
logs:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env logs -f

.PHONY: clean
clean:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml down -v
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml rm -f

# ============================================================================
# Development Commands
# ============================================================================

.PHONY: dev-up
dev-up:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml --env-file $(CURDIR)/.env up -d

.PHONY: dev-shell
dev-shell:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec backend /bin/bash

.PHONY: dev-db-shell
dev-db-shell:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

.PHONY: dev-migrate
dev-migrate:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec backend bash scripts/prestart.sh

.PHONY: dev-test
dev-test:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec backend bash scripts/test.sh

# ============================================================================
# Traefik Commands
# ============================================================================

.PHONY: traefik-up
traefik-up:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.traefik.yml up -d

.PHONY: traefik-down
traefik-down:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.traefik.yml down

# ============================================================================
# Code Quality Commands
# ============================================================================

.PHONY: format
format:
	@echo "Formatting backend code..."
	cd backend && uv run ruff format .
	@echo "Formatting frontend code..."
	cd frontend && npm run format

.PHONY: lint
lint:
	@echo "Linting backend code..."
	cd backend && uv run ruff check .
	@echo "Linting frontend code..."
	cd frontend && npm run lint

# ============================================================================
# Frontend Commands
# ============================================================================

.PHONY: frontend-build
frontend-build:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml build frontend

.PHONY: frontend-dev
frontend-dev:
	@echo "Starting frontend development server..."
	@echo "This will start the Vite dev server in the frontend directory."
	cd frontend && npm run dev

# ============================================================================
# Database Commands
# ============================================================================

.PHONY: db-shell
db-shell:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

.PHONY: db-migrate
db-migrate:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec backend bash scripts/prestart.sh

.PHONY: db-init
db-init:
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml exec backend python app/initial_data.py

# ============================================================================
# Cleanup Commands
# ============================================================================

.PHONY: clean-all
clean-all:
	@echo "Removing all containers..."
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml down -v
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml rm -f
	@echo "Removing all images..."
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.yml -f $(BUILD_DIR)/docker-compose.override.yml images -a --filter=until=0s -q | xargs -r docker rmi
	@echo "Cleaning Traefik stack..."
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.traefik.yml down -v
	$(COMPOSE) -f $(BUILD_DIR)/docker-compose.traefik.yml rm -f

.PHONY: prune
prune:
	@echo "Pruning unused Docker resources..."
	docker system prune -f
