# agent_with_backend/ Directory Structure

Generated on 2026-04-10

This document provides a complete overview of the project structure for the `agent_with_backend` directory.

## Full Tree Structure

```
agent_with_backend/
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── approval_controller.py
│   │   ├── drug_controller.py
│   │   ├── health_controller.py
│   │   └── order_controller.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── approval.py
│   │   ├── drug.py
│   │   └── order.py
│   ├── tests/
│   │   ├── test_approval_api.py
│   │   └── test_drug_api.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── drug_helpers.py
│   │   ├── logger.py
│   │   └── ros2_bridge.py
│   ├── __init__.py
│   ├── app.py
│   ├── approval.py
│   ├── init_db.py
│   ├── main.py
│   ├── pharmacy.db
│   ├── README.md
│   └── requirements.txt
├── docs/
│   ├── analysis/
│   │   └── backend-p1-integration-analysis.md
│   ├── guides/
│   │   ├── complete-workflow-test-guide.md
│   │   ├── doctor_cli.md
│   │   ├── project-structure.md
│   │   └── reference-manual.md
│   ├── superpowers/
│   │   ├── plans/
│   │   │   └── 2026-04-07-backend-p1-integration.md
│   │   └── specs/
│   │       ├── 2026-04-08-documentation-update-consolidation-design.md
│   │       └── 2026-04-08-project-reorganization-design.md
│   └── team/
│       ├── project-description-v3.md
│       ├── project-description-v4.md
│       ├── safety-guidelines.md
│       └── team-notice.md
├── P1/
│   ├── cli/
│   │   ├── example/
│   │   │   ├── agent_usage.py
│   │   │   └── http_client.py
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── doctor_cli.py
│   │   ├── interactive.py
│   │   ├── patient_cli.py
│   │   └── simple.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── workflows.py
│   ├── examples/
│   │   ├── __init__.py
│   │   ├── approve_prescription.md
│   │   ├── approve_prescription.py
│   │   ├── example_http_client.py
│   │   └── example_usage.py
│   ├── llm/
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── claude.py
│   │   │   └── openai.py
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── schemas.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── compressor.py
│   │   └── manager.py
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── run_p1_tests.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── pharmacy_client.py
│   ├── session/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── sessions/
│   ├── tests/
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_backend_integration.py
│   │   │   ├── test_deepseek_direct.py
│   │   │   ├── test_deepseek_integration.py
│   │   │   └── test_mocked_integration.py
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_core.py
│   │   ├── test_drug_db_integration.py
│   │   ├── test_drug_db_simple.py
│   │   ├── test_http_client.py
│   │   ├── test_inventory_integration.py
│   │   ├── test_medical_integration.py
│   │   ├── test_memory.py
│   │   ├── test_session.py
│   │   ├── test_tools.py
│   │   └── test_utils.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── executor.py
│   │   ├── inventory.py
│   │   ├── medical.py
│   │   ├── registry.py
│   │   └── report_generator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── http_client.py
│   │   ├── json_tools.py
│   │   ├── retry.py
│   │   ├── text_utils.py
│   │   └── validation.py
│   ├── .env.example
│   ├── __init__.py
│   ├── DEEPSEEK_CONFIG.md
│   ├── pytest.ini
│   ├── README.md
│   └── requirements.txt
├── scripts/
│   ├── setup/
│   │   ├── backend.lock
│   │   ├── cli-doctor-start.sh
│   │   ├── cli-patient-start.sh
│   │   └── init_db.py
│   ├── quick-start.sh
│   └── test-full-integration.py
├── sessions/
├── tests/
│   └── test_backend_config.py
├── .gitignore
├── backend.lock
├── conftest.py
├── Makefile
└── README.md
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `backend/` | Pharmacy backend system (FastAPI + SQLite) |
| `P1/` | Medical agent system with LLM integration |
| `docs/` | Project documentation and specifications |
| `scripts/` | Utility scripts for setup and testing |
| `tests/` | Integration and unit tests |
| `sessions/` | Session data storage |

## Excluded Items

The following items are excluded from this listing:
- `__pycache__/` directories
- Virtual environments (`venv/`, `.venv/`)
- Hidden files (except `.gitignore`, `.env.example`)
- Binary files and compiled Python files

---
*Last generated: 2026-04-10*  
*Python version: 3.12.3*