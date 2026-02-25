.PHONY: install dev run docker lint format clean test help

PYTHON  := python3
VENV    := venv
PIP     := $(VENV)/bin/pip
UV      := $(VENV)/bin/uvicorn
APP     := app.main:app

# ─────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  ClawPing — Developer Commands"
	@echo ""
	@echo "  make install   Create venv and install dependencies"
	@echo "  make dev       Start server with hot reload"
	@echo "  make run       Start server (production mode)"
	@echo "  make docker    Build and run with Docker Compose"
	@echo "  make lint      Check code style (black + isort)"
	@echo "  make format    Auto-format code (black + isort)"
	@echo "  make test      Run test suite"
	@echo "  make clean     Remove caches, venv, and db files"
	@echo ""

# ─────────────────────────────────────────────────────────
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed. Run 'make dev' to start."

# ─────────────────────────────────────────────────────────
dev:
	$(UV) $(APP) \
		--host $${API_HOST:-0.0.0.0} \
		--port $${API_PORT:-8000} \
		--reload

# ─────────────────────────────────────────────────────────
run:
	$(UV) $(APP) \
		--host $${API_HOST:-0.0.0.0} \
		--port $${API_PORT:-8000}

# ─────────────────────────────────────────────────────────
docker:
	docker compose up --build

docker-down:
	docker compose down

# ─────────────────────────────────────────────────────────
lint:
	$(VENV)/bin/black --check app/
	$(VENV)/bin/isort --check-only app/

format:
	$(VENV)/bin/black app/
	$(VENV)/bin/isort app/

# ─────────────────────────────────────────────────────────
test:
	$(VENV)/bin/pytest tests/ -v

# ─────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(VENV) dist build
	@echo "✓ Cleaned."
