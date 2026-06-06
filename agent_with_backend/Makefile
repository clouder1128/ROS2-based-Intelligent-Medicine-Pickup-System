# Makefile for Backend-P1 Integration Project

.PHONY: help test coverage test-integration cli-start backend-start backend-stop clean

help:
	@echo "Backend-P1 Integration Project Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  test              Run unit tests (mocked)"
	@echo "  coverage          Run tests and generate coverage_report/index.html"
	@echo "  patient           Start patient CLI"
	@echo "  doctor            Start doctor CLI"
	@echo "  backend-start      Start backend server"
	@echo "  backend-stop       Stop backend server"
	@echo "  clean              Clean up temporary files"
	@echo ""

test:
	@echo "Running unit tests..."
	@pytest tests/ -v --tb=short

coverage:
	@echo "Running tests with coverage..."
	@pytest tests/ -v --tb=short \
		--cov-config=.coveragerc \
		--cov \
		--cov-report=term-missing \
		--cov-report=html
	@echo "Coverage report: coverage_report/index.html"

patient:
	@echo "Starting patient cli..."
	@cd scripts/setup && ./cli-patient-start.sh

doctor:
	@echo "Starting doctor cli..."
	@cd scripts/setup && ./cli-doctor-start.sh

backend-start:
	@echo "Starting backend server..."
	@venv/bin/python main.py &

backend-stop:
	@echo "Stopping backend server..."
	@if pgrep -f "python3.*main\.py" > /dev/null; then \
		pkill -f "python3.*main\.py"; \
		echo "Backend stopped"; \
	else \
		echo "Backend not running"; \
	fi

clean:
	@echo "Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."
