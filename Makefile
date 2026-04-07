# Makefile for Backend-P1 Integration Project

.PHONY: help test-integration quick-start backend-start backend-stop clean

help:
	@echo "Backend-P1 Integration Project Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  test-integration   Run full integration test (requires backend running)"
	@echo "  quick-start        Start backend and P1 CLI in integrated mode"
	@echo "  backend-start      Start backend server"
	@echo "  backend-stop       Stop backend server"
	@echo "  clean              Clean up temporary files"
	@echo ""

test-integration:
	@echo "Running full integration test..."
	@cd scripts && python test-full-integration.py

quick-start:
	@echo "Starting integrated environment..."
	@chmod +x scripts/quick-start.sh
	@scripts/quick-start.sh

backend-start:
	@echo "Starting backend server..."
	@cd test/backend && python app.py &

backend-stop:
	@echo "Stopping backend server..."
	@pkill -f "python app.py" || true

clean:
	@echo "Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."