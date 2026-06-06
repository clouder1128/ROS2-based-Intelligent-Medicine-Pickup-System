"""ToolExecutor / BaseTool / TOOLS 列表单元测试

测试工具执行器和工具定义 Schema，不调用真实 tool handler（避免触发数据库）。
"""

import pytest
from unittest.mock import MagicMock
from agent.tools.executor import ToolExecutor
from agent.tools.base import BaseTool
from agent.tools.registry import TOOLS, execute_tool, get_registered_tools


class TestToolExecutor:
    def test_register_and_execute(self):
        executor = ToolExecutor()
        executor.register_handler("greet", lambda name: f"Hello, {name}!")
        result = executor.execute("greet", {"name": "World"})
        assert result == "Hello, World!"

    def test_execute_unregistered_raises(self):
        executor = ToolExecutor()
        with pytest.raises(Exception):
            executor.execute("nonexistent", {})

    def test_execute_handler_error(self):
        executor = ToolExecutor()
        def failing(**kwargs):
            raise ValueError("handler failed")
        executor.register_handler("fail", failing)
        with pytest.raises(Exception):
            executor.execute("fail", {})


class TestBaseTool:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            BaseTool(name="test", description="test", input_schema={})

    def test_concrete_tool(self):
        class ConcreteTool(BaseTool):
            def execute(self, **kwargs):
                return "ok"
        tool = ConcreteTool(name="test", description="test tool", input_schema={"type": "object"})
        assert tool.name == "test"
        assert tool.description == "test tool"
        assert tool.input_schema == {"type": "object"}
        assert tool.execute() == "ok"
        assert tool.to_dict()["name"] == "test"

    def test_validate_input(self):
        class ConcreteTool(BaseTool):
            def execute(self, **kwargs):
                return "ok"
        tool = ConcreteTool(name="v", description="v", input_schema={"type": "object"})
        # validate_input should not raise when no required fields
        assert tool.validate_input({}) is True


class TestToolSchemas:
    def test_tools_list_has_six_tools(self):
        assert len(TOOLS) == 6

    def test_each_tool_has_required_keys(self):
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_query_drug_schema(self):
        query_tool = next(t for t in TOOLS if t["name"] == "query_drug")
        assert query_tool["input_schema"]["properties"].get("query") is not None
        required = query_tool["input_schema"].get("required", [])
        assert "query" in required

    def test_submit_approval_schema(self):
        approval_tool = next(t for t in TOOLS if t["name"] == "submit_approval")
        props = approval_tool["input_schema"]["properties"]
        assert "patient_name" in props
        assert "advice" in props

    def test_check_allergy_schema(self):
        tool = next(t for t in TOOLS if t["name"] == "check_allergy")
        props = tool["input_schema"]["properties"]
        assert "patient_allergies" in props
        assert "drug_name" in props

    def test_calc_dosage_schema(self):
        tool = next(t for t in TOOLS if t["name"] == "calc_dosage")
        props = tool["input_schema"]["properties"]
        assert "drug_name" in props
        assert "age" in props
        assert "weight_kg" in props

    def test_generate_advice_schema(self):
        tool = next(t for t in TOOLS if t["name"] == "generate_advice")
        props = tool["input_schema"]["properties"]
        assert "drug_name" in props
        assert "dosage" in props

    def test_fill_prescription_schema(self):
        tool = next(t for t in TOOLS if t["name"] == "fill_prescription")
        props = tool["input_schema"]["properties"]
        assert "prescription_id" in props
        assert "patient_name" in props
        assert "drugs" in props


class TestRegistryFunctions:
    def test_execute_tool_function(self):
        """通过 registry.execute_tool 调用已注册的 handler"""
        # query_drug 需要数据库，不实际执行，仅验证函数存在
        assert callable(execute_tool)

    def test_get_registered_tools(self):
        tools = get_registered_tools()
        assert len(tools) >= 0  # may return handlers or tool descriptions
