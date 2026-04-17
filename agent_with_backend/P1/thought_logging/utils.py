# agent_with_backend/P1/thought_logging/utils.py
import os
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Union
import logging

logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """生成唯一的会话ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"

def format_timestamp(timestamp: float = None, format_str: str = "%Y-%m-%d %H:%M:%S.%f") -> str:
    """格式化时间戳为可读字符串"""
    if timestamp is None:
        timestamp = time.time()
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime(format_str)[:-3]  # 保留毫秒，去掉微秒

def safe_json_dumps(obj: Any, default=None) -> str:
    """安全的JSON序列化，处理无法序列化的对象"""

    def _default_serializer(o):
        """默认序列化器"""
        try:
            if default:
                return default(o)
            return str(o)
        except:
            return f"[{type(o).__name__}]"

    try:
        return json.dumps(obj, default=_default_serializer, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON序列化失败: {e}")
        return json.dumps({"error": f"序列化失败: {str(e)}"})

def ensure_directory(directory_path: str) -> bool:
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory_path}: {e}")
        return False

def get_current_time_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)

def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理敏感数据，避免日志中泄露敏感信息"""
    if not isinstance(data, dict):
        return data

    # 敏感字段关键字
    SENSITIVE_KEYS = [
        "password", "api_key", "token", "secret", "key",
        "credential", "auth", "authorization", "bearer",
        "private", "sensitive", "confidential"
    ]

    def _redact_value(key: str, value: Any) -> Any:
        """根据键名决定是否脱敏"""
        key_lower = key.lower()

        # 检查是否包含敏感关键词
        for sensitive in SENSITIVE_KEYS:
            if sensitive in key_lower:
                return "[REDACTED]"

        # 如果是字典或列表，递归处理
        if isinstance(value, dict):
            return sanitize_for_logging(value)
        elif isinstance(value, list):
            return [
                _redact_value(f"{key}_item", item) if isinstance(item, dict) else item
                for item in value
            ]

        return value

    result = {}
    for key, value in data.items():
        result[key] = _redact_value(key, value)

    return result