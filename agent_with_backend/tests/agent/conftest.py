"""agent 模块测试 conftest

设置最小环境变量（在 Config 被导入前生效）、添加 sys.path、
mock LLM 第三方包（anthropic / openai）、提供 mock fixtures。
"""

import os
import sys
from unittest.mock import MagicMock

# ── 将项目根目录加入 sys.path ──────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── 在 common.config.Config 被导入前设置 env vars ──────────────
# Config 以 class variable + os.getenv() 方式在导入时读取环境变量，
# 必须强制设好以避免读入 .env 文件中的值（load_dotenv 会覆盖 setdefault）。
os.environ["LLM_PROVIDER"] = "claude"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ENABLE_ROS2"] = "false"
os.environ["ENABLE_FORM_COLLECTION"] = "false"
os.environ["ENABLE_WORKFLOW_PLANNER"] = "false"
os.environ["ENABLE_LLM_SYMPTOM_EXTRACTION"] = "false"
os.environ["MAX_HISTORY_LEN"] = "50"
os.environ["MAX_ITERATIONS"] = "5"
os.environ["DATABASE_PATH"] = "/tmp/agent_test_pharmacy.db"

# ── Mock LLM 第三方包（防止 LLMClient 因 import 失败而抛出异常） ──
sys.modules["anthropic"] = MagicMock()
sys.modules["anthropic.Anthropic"] = MagicMock
sys.modules["openai"] = MagicMock()
sys.modules["openai.OpenAI"] = MagicMock

# ── Mock httpx（未安装，但 database.pharmacy_client 依赖它） ──
sys.modules["httpx"] = MagicMock()

# ── Mock database.pharmacy_client（内部依赖 httpx） ──
mock_pharmacy = MagicMock()
mock_pharmacy.query_drugs_by_symptom.return_value = []
mock_pharmacy.query_drug_by_name.return_value = None
sys.modules["database.pharmacy_client"] = mock_pharmacy

import pytest


@pytest.fixture(autouse=True)
def agent_env(monkeypatch):
    """每个测试前覆盖 env vars 和 Config 类属性（防止其他测试污染）。"""
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_FORM_COLLECTION", "false")
    monkeypatch.setenv("ENABLE_LLM_SYMPTOM_EXTRACTION", "false")
    monkeypatch.setenv("MAX_HISTORY_LEN", "50")
    monkeypatch.setenv("MAX_ITERATIONS", "5")

    # Config 类属性在模块导入时已通过 os.getenv 求值，需直接 patch
    from common.config import Config
    monkeypatch.setattr(Config, "LLM_PROVIDER", "claude")
    monkeypatch.setattr(Config, "ENABLE_FORM_COLLECTION", False)
    monkeypatch.setattr(Config, "ENABLE_LLM_SYMPTOM_EXTRACTION", False)
    monkeypatch.setattr(Config, "ENABLE_WORKFLOW_PLANNER", False)
    monkeypatch.setattr(Config, "MAX_HISTORY_LEN", 50)
    monkeypatch.setattr(Config, "MAX_ITERATIONS", 5)


@pytest.fixture
def mock_llm_client():
    """返回一个模拟 LLMClient，chat() 返回无 tool_calls 的响应。"""
    client = MagicMock()
    client.chat.return_value = {
        "content": "根据您的症状，建议您使用布洛芬。",
        "tool_calls": [],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    client.chat_structured.return_value = MagicMock(
        content="测试响应",
        tool_calls=[],
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    return client


@pytest.fixture
def mock_message_manager():
    """返回一个模拟 MessageManager。"""
    mgr = MagicMock()
    mgr.get_messages.return_value = []
    mgr.get_full_messages.return_value = [
        {"role": "system", "content": "你是医疗助手"}
    ]
    return mgr
