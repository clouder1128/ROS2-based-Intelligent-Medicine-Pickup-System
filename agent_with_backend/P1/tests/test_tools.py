import json
import pytest
from unittest.mock import Mock, patch
from tools.registry import (
    register_tool_handler,
    execute_tool,
    is_tool_registered,
    get_executor,
)
from core.exceptions import ToolExecutionError


def test_base_tool_creation():
    """测试BaseTool创建和验证"""
    from tools.base import BaseTool

    class MockTool(BaseTool):
        def execute(self, **kwargs):
            return "mock result"

    tool = MockTool(
        name="test_tool",
        description="测试工具",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )

    assert tool.name == "test_tool"
    assert tool.validate_input({"query": "test"}) == True
    assert tool.validate_input({}) == False


# ==================== Mock工具（模拟P2/P4的实现） ====================
def mock_query_drug(query: str) -> str:
    return json.dumps(
        [
            {
                "name": "阿莫西林",
                "specification": "500mg/粒",
                "stock": 100,
                "is_prescription": True,
            },
            {
                "name": "布洛芬",
                "specification": "200mg/粒",
                "stock": 50,
                "is_prescription": False,
            },
        ]
    )


def mock_check_allergy(patient_allergies: str, drug_name: str) -> str:
    if "青霉素" in patient_allergies and drug_name == "阿莫西林":
        return json.dumps(
            {"allergic": True, "message": "患者对青霉素类过敏，禁止使用阿莫西林"}
        )
    return json.dumps({"allergic": False, "message": "无已知过敏"})


def mock_calc_dosage(
    drug_name: str, age: int, weight_kg: float, condition_severity: str = "中"
) -> str:
    if drug_name == "阿莫西林":
        dosage = f"{500 * (weight_kg / 70):.0f}mg，每日2次"
    else:
        dosage = "请遵医嘱"
    return json.dumps({"dosage": dosage, "unit": "mg"})


def mock_generate_advice(
    drug_name: str, dosage: str, duration: str = "3天", notes: str = ""
) -> str:
    advice = f"建议使用{drug_name}，剂量{dosage}，疗程{duration}。{notes}"
    return json.dumps({"advice_text": advice})


def mock_submit_approval(
    patient_name: str,
    symptoms: str,
    advice_text: str,
    drug_name: str,
    patient_age: int = None,
    patient_weight: float = None,
    drug_type: str = "prescription",
) -> str:
    from utils.text_utils import generate_id

    approval_id = generate_id("AP")
    return json.dumps({"approval_id": approval_id, "status": "pending"})


def mock_fill_prescription(prescription_id: str, patient_name: str, drugs: list) -> str:
    return json.dumps({"pickup_code": f"PC-{prescription_id[:8]}"})


def register_mock_handlers() -> None:
    register_tool_handler("query_drug", mock_query_drug)
    register_tool_handler("check_allergy", mock_check_allergy)
    register_tool_handler("calc_dosage", mock_calc_dosage)
    register_tool_handler("generate_advice", mock_generate_advice)
    register_tool_handler("submit_approval", mock_submit_approval)
    register_tool_handler("fill_prescription", mock_fill_prescription)


class TestToolRegistry:
    """测试工具注册和执行功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理工具处理器
        executor = get_executor()
        executor._handlers.clear()
        register_mock_handlers()

    def test_tool_registration(self):
        """测试工具注册机制"""

        def dummy_handler(x: str) -> str:
            return x

        register_tool_handler("dummy_tool", dummy_handler)
        assert "dummy_tool" in get_executor()._handlers
        assert is_tool_registered("dummy_tool")

    def test_execute_tool(self):
        """测试工具执行"""
        result = execute_tool("query_drug", {"query": "感冒"})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_exception_handling(self):
        """测试异常处理"""

        def bad_tool() -> None:
            raise ValueError("模拟错误")

        register_tool_handler("bad_tool", bad_tool)
        with pytest.raises(ToolExecutionError):
            execute_tool("bad_tool", {})
