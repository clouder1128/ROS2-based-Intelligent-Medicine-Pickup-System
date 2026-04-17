# tests/thought_logging/test_utils.py
import time
import json
from datetime import datetime
from agent_with_backend.P1.thought_logging.utils import (
    generate_session_id,
    format_timestamp,
    safe_json_dumps,
    ensure_directory,
    get_current_time_ms,
    sanitize_for_logging
)

def test_generate_session_id():
    """测试生成会话ID"""
    session_id = generate_session_id()
    assert session_id.startswith("session_")
    assert len(session_id) > 20

    # 第二个ID应该不同
    session_id2 = generate_session_id()
    assert session_id != session_id2

def test_format_timestamp():
    """测试时间戳格式化"""
    ts = 1713321851.858
    formatted = format_timestamp(ts)
    assert "2024" in formatted  # 时间戳1713321851.858对应2024年

    # 测试默认参数
    formatted_now = format_timestamp()
    assert len(formatted_now) == len(formatted)

def test_safe_json_dumps():
    """测试安全的JSON序列化"""
    data = {
        "name": "test",
        "value": 123,
        "nested": {"key": "value"},
        "timestamp": time.time()
    }

    json_str = safe_json_dumps(data)
    parsed = json.loads(json_str)
    assert parsed["name"] == "test"
    assert parsed["value"] == 123

    # 测试无法序列化的对象
    class Unserializable:
        pass

    data["unserializable"] = Unserializable()
    json_str = safe_json_dumps(data)
    parsed = json.loads(json_str)
    assert "unserializable" in parsed
    # 当前实现使用str(o)序列化对象，所以会得到对象的字符串表示
    assert "Unserializable object at" in parsed["unserializable"]

def test_ensure_directory():
    """测试目录创建"""
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    test_dir = f"{temp_dir}/test/sub/dir"

    # 目录不存在时创建
    result = ensure_directory(test_dir)
    assert result == True
    import os
    assert os.path.exists(test_dir)

    # 目录已存在时返回True
    result = ensure_directory(test_dir)
    assert result == True

    # 清理
    shutil.rmtree(temp_dir)

def test_sanitize_for_logging():
    """测试日志数据清理"""
    data = {
        "password": "secret123",
        "api_key": "sk-123456",
        "token": "eyJhbGciOiJIUzI1NiIs",
        "safe_data": "正常数据",
        "nested": {
            "secret": "confidential",
            "public": "公开信息"
        }
    }

    sanitized = sanitize_for_logging(data)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["safe_data"] == "正常数据"
    assert sanitized["nested"]["secret"] == "[REDACTED]"
    assert sanitized["nested"]["public"] == "公开信息"

def test_get_current_time_ms():
    """测试获取当前时间戳（毫秒）"""
    ts1 = get_current_time_ms()
    import time
    time.sleep(0.001)  # 等待1毫秒
    ts2 = get_current_time_ms()

    assert ts2 > ts1  # 确保时间在前进
    assert isinstance(ts1, int)  # 确保返回的是整数

    # 验证是毫秒级时间戳（应该在合理范围内）
    current_seconds = time.time()
    current_millis = int(current_seconds * 1000)
    assert abs(ts1 - current_millis) < 1000  # 误差应该在1秒内