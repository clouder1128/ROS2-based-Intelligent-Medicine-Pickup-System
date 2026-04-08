# test_utils.py
"""工具函数模块测试"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

# 导入要测试的工具函数
from utils.text_utils import (
    truncate_text,
    estimate_tokens,
    log_duration,
    generate_id,
    hash_string,
    now_iso,
    safe_get,
    merge_dicts,
    validate_patient_input,
    extract_mentions_of_allergy,
    summarize_conversation,
    estimate_cost,
)

from utils.json_tools import extract_json_from_text, safe_parse_json, format_tool_result

from utils.retry import retry_on_exception
from utils.validation import create_error_response, create_success_response


class TestTextUtils:
    """文本工具函数测试"""

    def test_truncate_text(self):
        """测试文本截断"""
        # 短文本不截断
        assert truncate_text("hello", 10) == "hello"
        # 长文本截断
        result = truncate_text("hello world this is a long text", 15)
        assert len(result) == 15
        assert result.endswith("...")
        # 边界情况
        assert truncate_text("", 10) == ""

    def test_estimate_tokens(self):
        """测试token估算"""
        assert estimate_tokens("hello") == 1  # 5 // 4 = 1
        assert estimate_tokens("hello world") == 2  # 11 // 4 = 2
        assert estimate_tokens("") == 0

    def test_generate_id(self):
        """测试ID生成"""
        # 模拟datetime.now返回不同的时间，确保ID不同
        from datetime import datetime
        from unittest.mock import patch

        with patch("utils.text_utils.datetime") as mock_datetime:
            # 设置两次不同的返回值
            mock_datetime.now.side_effect = [
                datetime(2024, 1, 1, 10, 30, 15),
                datetime(2024, 1, 1, 10, 30, 16),
            ]

            id1 = generate_id("TEST")
            id2 = generate_id("TEST")

        # 格式检查
        assert id1.startswith("TEST-")
        assert len(id1) == len("TEST-20240101-103015")
        assert id2.startswith("TEST-")
        assert len(id2) == len("TEST-20240101-103016")
        # 两个ID应该不同（时间不同）
        assert id1 != id2
        assert id1 == "TEST-20240101-103015"
        assert id2 == "TEST-20240101-103016"

    def test_hash_string(self):
        """测试字符串哈希"""
        hash1 = hash_string("hello")
        hash2 = hash_string("hello")
        hash3 = hash_string("world")

        assert len(hash1) == 8  # 8位哈希
        assert hash1 == hash2  # 相同输入相同输出
        assert hash1 != hash3  # 不同输入不同输出

    def test_now_iso(self):
        """测试ISO时间格式"""
        iso_time = now_iso()
        # 检查格式 - 应该是有效的ISO格式字符串
        assert "T" in iso_time
        # 尝试解析为datetime对象验证格式
        from datetime import datetime

        parsed = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_safe_get(self):
        """测试安全获取嵌套字典值"""
        data = {"a": {"b": {"c": 123}}}

        assert safe_get(data, "a.b.c") == 123
        assert safe_get(data, "a.b.d") is None
        assert safe_get(data, "a.b.d", "default") == "default"
        assert safe_get(data, "x.y.z") is None
        assert safe_get({}, "a.b.c") is None

    def test_merge_dicts(self):
        """测试字典合并"""
        base = {"a": 1, "b": {"x": 10, "y": 20}}
        updates = {"b": {"y": 30, "z": 40}, "c": 3}

        result = merge_dicts(base, updates)
        assert result["a"] == 1
        assert result["b"]["x"] == 10  # 保留base的值
        assert result["b"]["y"] == 30  # 被updates覆盖
        assert result["b"]["z"] == 40  # 新增
        assert result["c"] == 3

    def test_validate_patient_input(self):
        """测试患者输入验证"""
        # 有效输入
        result = validate_patient_input("我头痛")
        assert result["valid"] is True
        assert "cleaned" in result

        # 空输入
        result = validate_patient_input("")
        assert result["valid"] is False
        assert "error" in result

        # 太短
        result = validate_patient_input("a")
        assert result["valid"] is False

        # 敏感词
        result = validate_patient_input("我想自杀")
        assert result["valid"] is False
        assert "敏感词" in result["error"]

    def test_extract_mentions_of_allergy(self):
        """测试过敏物质提取"""
        text = "我对青霉素和头孢过敏"
        result = extract_mentions_of_allergy(text)
        assert "青霉素" in result
        assert "头孢" in result
        assert len(result) == 2

        # 无过敏提及
        result = extract_mentions_of_allergy("我头痛")
        assert result == []

    def test_summarize_conversation(self):
        """测试对话摘要"""
        messages = [
            {"role": "user", "content": "我头痛"},
            {"role": "assistant", "content": "建议休息"},
            {"role": "user", "content": "还发烧"},
            {"role": "assistant", "content": "建议就医"},
        ]

        summary = summarize_conversation(messages)
        assert "患者诉求" in summary
        assert "头痛" in summary or "发烧" in summary

        # 空对话
        assert summarize_conversation([]) == "无对话记录"

    def test_estimate_cost(self):
        """测试费用估算"""
        # 默认模型
        cost = estimate_cost(1000)
        assert isinstance(cost, float)
        assert cost > 0

        # 不同模型
        cost_gpt4 = estimate_cost(1000, "gpt-4")
        cost_gpt35 = estimate_cost(1000, "gpt-3.5-turbo")
        assert cost_gpt4 > cost_gpt35  # GPT-4应该更贵

        # 未知模型使用默认价格
        cost_unknown = estimate_cost(1000, "unknown-model")
        assert cost_unknown == estimate_cost(1000, "claude-3-sonnet")

    def test_log_duration(self):
        """测试耗时日志记录器"""
        import logging

        logger = logging.getLogger(__name__)
        with patch.object(logger, "info") as mock_info:
            with log_duration(logger, "测试操作"):
                time.sleep(0.01)  # 短暂等待

            # 检查是否记录了耗时
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "测试操作" in call_args
            assert "took" in call_args


class TestJsonTools:
    """JSON工具函数测试"""

    def test_extract_json_from_text(self):
        """测试从文本提取JSON"""
        # 包含JSON的文本
        text = '这是文本```json{"name": "test", "value": 123}```更多文本'
        result = extract_json_from_text(text)
        assert result == {"name": "test", "value": 123}

        # 无效JSON
        text = '```json{"invalid": json}```'
        result = extract_json_from_text(text)
        assert result is None

        # 无JSON
        result = extract_json_from_text("纯文本")
        assert result is None

    def test_safe_parse_json(self):
        """测试安全解析JSON"""
        # 有效JSON
        result = safe_parse_json('{"a": 1, "b": "test"}')
        assert result == {"a": 1, "b": "test"}

        # 无效JSON
        result = safe_parse_json("{invalid json}")
        assert result is None

        # 空字符串
        result = safe_parse_json("")
        assert result is None

    def test_format_tool_result(self):
        """测试工具结果格式化"""
        # 字典
        result = format_tool_result({"a": 1, "b": "test"})
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["a"] == 1

        # 列表
        result = format_tool_result([1, 2, 3])
        assert isinstance(result, str)
        data = json.loads(result)
        assert data == [1, 2, 3]

        # 字符串
        result = format_tool_result("hello")
        assert result == "hello"

        # 数字
        result = format_tool_result(123)
        assert result == "123"


class TestRetry:
    """重试装饰器测试"""

    def test_retry_on_exception_success(self):
        """测试重试装饰器 - 成功情况"""
        call_count = 0

        @retry_on_exception(ValueError, max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_exception_failure(self):
        """测试重试装饰器 - 失败情况"""
        call_count = 0

        @retry_on_exception(ValueError, max_retries=3, delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("模拟错误")

        with pytest.raises(ValueError):
            failing_func()

        assert call_count == 3  # 重试3次

    def test_retry_on_exception_recovery(self):
        """测试重试装饰器 - 恢复情况"""
        call_count = 0

        @retry_on_exception(ValueError, max_retries=3, delay=0.01)
        def recovering_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("前两次失败")
            return "success"

        result = recovering_func()
        assert result == "success"
        assert call_count == 2


class TestValidation:
    """验证工具函数测试"""

    def test_create_error_response(self):
        """测试错误响应创建"""
        response = create_error_response("validation_error", "输入无效")

        assert response["success"] is False
        assert response["error_type"] == "validation_error"
        assert response["message"] == "输入无效"

        # 检查必需字段
        assert all(key in response for key in ["success", "error_type", "message"])

    def test_create_success_response(self):
        """测试成功响应创建"""
        test_data = {"id": 123, "name": "test"}
        response = create_success_response(test_data)

        assert response["success"] is True
        assert response["data"] == test_data

        # 检查必需字段
        assert all(key in response for key in ["success", "data"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
