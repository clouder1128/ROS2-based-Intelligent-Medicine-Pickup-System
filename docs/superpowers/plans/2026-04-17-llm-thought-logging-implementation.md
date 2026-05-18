# LLM思考记录系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为医疗助手Agent添加LLM思考过程记录功能，捕获完整的思考过程并以两种格式（JSON和文本）输出到日志文件夹

**Architecture:** 采用装饰器模式包装现有类（MedicalAgent, LLMClient），通过ThoughtRecorder收集数据，OutputManager协调JSONFileWriter和TextFileWriter输出两种格式日志，配置系统控制功能开关

**Tech Stack:** Python 3.8+, 装饰器模式，JSON序列化，Python logging扩展，环境变量配置

---

## 文件结构

### 新文件
- `agent_with_backend/P1/thought_logging/__init__.py` - 包初始化
- `agent_with_backend/P1/thought_logging/recorder.py` - ThoughtRecorder核心类
- `agent_with_backend/P1/thought_logging/output.py` - OutputManager和文件写入器
- `agent_with_backend/P1/thought_logging/decorators.py` - 装饰器实现
- `agent_with_backend/P1/thought_logging/config.py` - 配置管理
- `agent_with_backend/P1/thought_logging/utils.py` - 工具函数
- `tests/thought_logging/test_recorder.py` - ThoughtRecorder测试
- `tests/thought_logging/test_output.py` - OutputManager测试
- `tests/thought_logging/test_decorators.py` - 装饰器测试
- `tests/thought_logging/test_config.py` - 配置测试

### 修改文件
- `agent_with_backend/P1/core/config.py` - 添加思考记录配置项
- `agent_with_backend/P1/cli/interactive.py` - 集成思考记录功能

### 配置文件
- `.thought_logging.env` - 思考记录配置示例文件
- `docs/thought_logging_usage.md` - 使用说明文档

---

### Task 1: 项目结构设置和配置系统

**Files:**
- Create: `agent_with_backend/P1/thought_logging/__init__.py`
- Create: `agent_with_backend/P1/thought_logging/config.py`
- Modify: `agent_with_backend/P1/core/config.py:35-50`
- Test: `tests/thought_logging/test_config.py`

- [ ] **Step 1: 创建thought_logging包结构**

```bash
mkdir -p agent_with_backend/P1/thought_logging
mkdir -p tests/thought_logging
touch agent_with_backend/P1/thought_logging/__init__.py
```

- [ ] **Step 2: 编写配置测试**

```python
# tests/thought_logging/test_config.py
import os
import pytest
from unittest.mock import patch
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_config_defaults():
    """测试配置默认值"""
    config = ThoughtLoggingConfig()
    assert config.enabled == False
    assert config.log_level == "DETAILED"
    assert config.log_to_file == True
    assert config.log_to_console == False

def test_config_from_env():
    """测试从环境变量加载配置"""
    with patch.dict(os.environ, {
        "ENABLE_THOUGHT_LOGGING": "true",
        "THOUGHT_LOG_LEVEL": "DEBUG",
        "THOUGHT_LOG_TO_CONSOLE": "true"
    }):
        config = ThoughtLoggingConfig()
        assert config.enabled == True
        assert config.log_level == "DEBUG"
        assert config.log_to_console == True

def test_config_validation():
    """测试配置验证"""
    config = ThoughtLoggingConfig()
    config.log_level = "INVALID"
    with pytest.raises(ValueError):
        config.validate()
```

- [ ] **Step 3: 运行测试验证失败**

Run: `pytest tests/thought_logging/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_with_backend.P1.thought_logging.config'"

- [ ] **Step 4: 创建配置类**

```python
# agent_with_backend/P1/thought_logging/config.py
import os
import logging
from typing import List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ThoughtLoggingConfig:
    """思考记录配置类"""
    
    enabled: bool = False
    log_level: str = "DETAILED"
    log_to_file: bool = True
    log_to_console: bool = False
    log_dir: str = "./logs/thoughts"
    log_formats: List[str] = field(default_factory=lambda: ["json", "text"])
    session_auto_cleanup: bool = True
    session_retention_days: int = 7
    
    # 支持的日志级别
    _SUPPORTED_LEVELS = ["BASIC", "STANDARD", "DETAILED", "DEBUG"]
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self._load_from_env()
        self.validate()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            "ENABLE_THOUGHT_LOGGING": ("enabled", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_LEVEL": ("log_level", str),
            "THOUGHT_LOG_TO_FILE": ("log_to_file", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_TO_CONSOLE": ("log_to_console", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_DIR": ("log_dir", str),
            "THOUGHT_LOG_FORMATS": ("log_formats", lambda x: [f.strip() for f in x.split(",")]),
            "THOUGHT_SESSION_AUTO_CLEANUP": ("session_auto_cleanup", lambda x: x.lower() == "true"),
            "THOUGHT_SESSION_RETENTION_DAYS": ("session_retention_days", int),
        }
        
        for env_var, (attr_name, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    setattr(self, attr_name, converter(value))
                except (ValueError, TypeError) as e:
                    logger.warning(f"无法解析环境变量 {env_var}={value}: {e}")
    
    def validate(self):
        """验证配置有效性"""
        if self.log_level not in self._SUPPORTED_LEVELS:
            raise ValueError(
                f"无效的日志级别: {self.log_level}, 必须是 {self._SUPPORTED_LEVELS}"
            )
        
        if not isinstance(self.log_formats, list):
            raise ValueError("log_formats必须是列表")
        
        supported_formats = ["json", "text"]
        for fmt in self.log_formats:
            if fmt not in supported_formats:
                raise ValueError(
                    f"不支持的日志格式: {fmt}, 必须是 {supported_formats}"
                )
        
        # 确保日志目录存在
        if self.log_to_file:
            os.makedirs(self.log_dir, exist_ok=True)
    
    def to_dict(self):
        """转换为字典（不包含敏感信息）"""
        return {
            "enabled": self.enabled,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_to_console": self.log_to_console,
            "log_dir": self.log_dir,
            "log_formats": self.log_formats,
            "session_auto_cleanup": self.session_auto_cleanup,
            "session_retention_days": self.session_retention_days,
        }
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/thought_logging/test_config.py -v`
Expected: PASS

- [ ] **Step 6: 修改主配置类添加思考记录配置**

```python
# agent_with_backend/P1/core/config.py:35-50
# 在Config类中添加以下配置项

    # 思考记录配置
    ENABLE_THOUGHT_LOGGING = os.getenv("ENABLE_THOUGHT_LOGGING", "false").lower() == "true"
    THOUGHT_LOG_LEVEL = os.getenv("THOUGHT_LOG_LEVEL", "DETAILED")
    THOUGHT_LOG_TO_FILE = os.getenv("THOUGHT_LOG_TO_FILE", "true").lower() == "true"
    THOUGHT_LOG_TO_CONSOLE = os.getenv("THOUGHT_LOG_TO_CONSOLE", "false").lower() == "true"
    THOUGHT_LOG_DIR = os.getenv("THOUGHT_LOG_DIR", "./logs/thoughts")
    THOUGHT_LOG_FORMATS = os.getenv("THOUGHT_LOG_FORMATS", "json,text").split(",")
    THOUGHT_SESSION_AUTO_CLEANUP = os.getenv("THOUGHT_SESSION_AUTO_CLEANUP", "true").lower() == "true"
    THOUGHT_SESSION_RETENTION_DAYS = int(os.getenv("THOUGHT_SESSION_RETENTION_DAYS", "7"))

# 在validate方法中添加验证（第90-102行后添加）
        # 验证思考记录配置
        if cls.THOUGHT_LOG_LEVEL not in ["BASIC", "STANDARD", "DETAILED", "DEBUG"]:
            raise ConfigurationError(
                f"无效的THOUGHT_LOG_LEVEL: {cls.THOUGHT_LOG_LEVEL}, 必须是 BASIC, STANDARD, DETAILED 或 DEBUG"
            )
        
        if not all(fmt in ["json", "text"] for fmt in cls.THOUGHT_LOG_FORMATS):
            raise ConfigurationError(
                f"无效的THOUGHT_LOG_FORMATS: {cls.THOUGHT_LOG_FORMATS}, 只能包含 json 和 text"
            )
        
        if cls.THOUGHT_SESSION_RETENTION_DAYS <= 0:
            raise ConfigurationError(
                f"THOUGHT_SESSION_RETENTION_DAYS必须大于0，当前值: {cls.THOUGHT_SESSION_RETENTION_DAYS}"
            )
```

- [ ] **Step 7: 运行配置验证测试**

Run: `pytest agent_with_backend/P1/tests/ -k config -v`
Expected: PASS（现有测试应继续通过）

- [ ] **Step 8: 提交**

```bash
git add agent_with_backend/P1/thought_logging/ agent_with_backend/P1/core/config.py tests/thought_logging/
git commit -m "feat: add thought logging configuration system"
```

---

### Task 2: 工具函数和会话管理

**Files:**
- Create: `agent_with_backend/P1/thought_logging/utils.py`
- Test: `tests/thought_logging/test_utils.py`

- [ ] **Step 1: 编写工具函数测试**

```python
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
    assert "2026" in formatted  # 当前年份
    
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
    assert "[Unserializable]" in parsed["unserializable"]

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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/thought_logging/test_utils.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_with_backend.P1.thought_logging.utils'"

- [ ] **Step 3: 实现工具函数**

```python
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/thought_logging/test_utils.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agent_with_backend/P1/thought_logging/utils.py tests/thought_logging/test_utils.py
git commit -m "feat: add thought logging utility functions"
```

---

### Task 3: ThoughtRecorder核心类

**Files:**
- Create: `agent_with_backend/P1/thought_logging/recorder.py`
- Test: `tests/thought_logging/test_recorder.py`

- [ ] **Step 1: 编写ThoughtRecorder测试**

```python
# tests/thought_logging/test_recorder.py
import time
import json
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging.recorder import ThoughtRecorder
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_recorder_initialization():
    """测试记录器初始化"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    assert recorder.enabled == True
    assert recorder.config == config
    assert recorder.session_id is not None
    assert recorder.thoughts == []
    assert recorder.current_iteration == 0

def test_recorder_disabled():
    """测试禁用状态的记录器"""
    config = ThoughtLoggingConfig(enabled=False)
    recorder = ThoughtRecorder(config)
    
    # 当禁用时，记录方法应该不存储数据
    recorder.record_llm_call(0, ["msg1", "msg2"], {"content": "response"})
    assert len(recorder.thoughts) == 0
    
    # 但应该仍然有session_id
    assert recorder.session_id is not None

def test_record_llm_call():
    """测试记录LLM调用"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "测试消息"}
    ]
    response = {
        "content": "调用工具",
        "tool_calls": [{"name": "query_drug", "input": {"症状": "头疼"}}]
    }
    metadata = {"provider": "claude", "model": "claude-3-sonnet"}
    
    recorder.record_llm_call(1, messages, response, metadata)
    
    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]
    
    assert thought["type"] == "llm_call"
    assert thought["iteration"] == 1
    assert thought["messages"] == messages
    assert thought["response"] == response
    assert thought["metadata"]["provider"] == "claude"
    assert "timestamp" in thought
    assert "session_id" in thought

def test_record_tool_decision():
    """测试记录工具调用决策"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    tool_name = "query_drug"
    input_data = {"症状": "头疼"}
    reasoning = "根据症状查询相关药物"
    result = {"drugs": ["布洛芬"]}
    
    recorder.record_tool_decision(2, tool_name, input_data, reasoning, result)
    
    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]
    
    assert thought["type"] == "tool_decision"
    assert thought["iteration"] == 2
    assert thought["tool_name"] == tool_name
    assert thought["input"] == input_data
    assert thought["reasoning"] == reasoning
    assert thought["result"] == result

def test_record_iteration_state():
    """测试记录迭代状态"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    state = {
        "messages_count": 5,
        "tools_called": ["query_drug"],
        "workflow_step": "query_drug"
    }
    
    recorder.record_iteration_state(3, state)
    
    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]
    
    assert thought["type"] == "iteration_state"
    assert thought["iteration"] == 3
    assert thought["state"] == state

def test_get_thoughts_by_type():
    """测试按类型获取思考记录"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    # 添加多种类型的记录
    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool", {}, "reason", {})
    recorder.record_llm_call(2, [], {})
    recorder.record_iteration_state(2, {})
    
    llm_calls = recorder.get_thoughts_by_type("llm_call")
    assert len(llm_calls) == 2
    
    tool_decisions = recorder.get_thoughts_by_type("tool_decision")
    assert len(tool_decisions) == 1
    
    iteration_states = recorder.get_thoughts_by_type("iteration_state")
    assert len(iteration_states) == 1

def test_clear_thoughts():
    """测试清空思考记录"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool", {}, "reason", {})
    
    assert len(recorder.thoughts) == 2
    
    recorder.clear_thoughts()
    assert len(recorder.thoughts) == 0
    assert recorder.current_iteration == 0

def test_update_iteration():
    """测试更新迭代计数器"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)
    
    assert recorder.current_iteration == 0
    
    recorder.update_iteration(5)
    assert recorder.current_iteration == 5
    
    # 记录应该使用新的迭代号
    recorder.record_llm_call(None, [], {})
    assert recorder.thoughts[0]["iteration"] == 5
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/thought_logging/test_recorder.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_with_backend.P1.thought_logging.recorder'"

- [ ] **Step 3: 实现ThoughtRecorder类**

```python
# agent_with_backend/P1/thought_logging/recorder.py
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .config import ThoughtLoggingConfig
from .utils import generate_session_id, format_timestamp, sanitize_for_logging

logger = logging.getLogger(__name__)

@dataclass
class ThoughtRecorder:
    """思考记录器核心类"""
    
    config: ThoughtLoggingConfig
    enabled: bool = field(init=False)
    session_id: str = field(init=False)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    current_iteration: int = 0
    
    def __post_init__(self):
        """初始化后设置"""
        self.enabled = self.config.enabled
        self.session_id = generate_session_id()
        logger.debug(f"ThoughtRecorder初始化，会话ID: {self.session_id}")
    
    def record_llm_call(
        self,
        iteration: Optional[int],
        messages: List[Dict[str, str]],
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录一次LLM调用
        
        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            messages: 输入消息列表
            response: LLM响应
            metadata: 元数据（provider, model, thinking_content等）
        """
        if not self.enabled:
            return
        
        try:
            thought = {
                "type": "llm_call",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "messages": sanitize_for_logging(messages),
                "response": sanitize_for_logging(response),
                "tool_calls": response.get("tool_calls", []),
                "metadata": {
                    "provider": metadata.get("provider") if metadata else None,
                    "model": metadata.get("model") if metadata else None,
                    "thinking_supported": metadata.get("thinking_supported", False) if metadata else False,
                    "thinking_content": metadata.get("thinking_content") if metadata else None,
                    "duration_ms": metadata.get("duration_ms") if metadata else None,
                    "estimated_tokens": metadata.get("estimated_tokens") if metadata else None,
                }
            }
            
            # 清理元数据中的None值
            thought["metadata"] = {
                k: v for k, v in thought["metadata"].items() 
                if v is not None
            }
            
            self.thoughts.append(thought)
            logger.debug(f"记录LLM调用，迭代: {thought['iteration']}")
            
        except Exception as e:
            logger.error(f"记录LLM调用失败: {e}", exc_info=True)
    
    def record_tool_decision(
        self,
        iteration: Optional[int],
        tool_name: str,
        input_data: Dict[str, Any],
        reasoning: Optional[str],
        result: Dict[str, Any]
    ) -> None:
        """记录工具调用决策
        
        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            tool_name: 工具名称
            input_data: 输入参数
            reasoning: 调用理由
            result: 工具执行结果
        """
        if not self.enabled:
            return
        
        try:
            thought = {
                "type": "tool_decision",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "tool_name": tool_name,
                "input": sanitize_for_logging(input_data),
                "reasoning": reasoning,
                "result": sanitize_for_logging(result),
            }
            
            self.thoughts.append(thought)
            logger.debug(f"记录工具调用决策: {tool_name}")
            
        except Exception as e:
            logger.error(f"记录工具调用决策失败: {e}", exc_info=True)
    
    def record_iteration_state(
        self,
        iteration: Optional[int],
        state: Dict[str, Any]
    ) -> None:
        """记录迭代状态
        
        Args:
            iteration: 迭代号，如果为None则使用current_iteration
            state: 状态信息
        """
        if not self.enabled:
            return
        
        try:
            thought = {
                "type": "iteration_state",
                "timestamp": time.time(),
                "formatted_timestamp": format_timestamp(),
                "session_id": self.session_id,
                "iteration": iteration if iteration is not None else self.current_iteration,
                "state": sanitize_for_logging(state),
            }
            
            self.thoughts.append(thought)
            logger.debug(f"记录迭代状态，迭代: {thought['iteration']}")
            
        except Exception as e:
            logger.error(f"记录迭代状态失败: {e}", exc_info=True)
    
    def get_thoughts_by_type(self, thought_type: str) -> List[Dict[str, Any]]:
        """按类型获取思考记录
        
        Args:
            thought_type: 记录类型（llm_call, tool_decision, iteration_state）
            
        Returns:
            该类型的所有记录
        """
        return [t for t in self.thoughts if t["type"] == thought_type]
    
    def get_thoughts_by_iteration(self, iteration: int) -> List[Dict[str, Any]]:
        """按迭代号获取思考记录
        
        Args:
            iteration: 迭代号
            
        Returns:
            该迭代的所有记录
        """
        return [t for t in self.thoughts if t["iteration"] == iteration]
    
    def clear_thoughts(self) -> None:
        """清空所有思考记录"""
        self.thoughts.clear()
        logger.debug("已清空所有思考记录")
    
    def update_iteration(self, iteration: int) -> None:
        """更新当前迭代号
        
        Args:
            iteration: 新的迭代号
        """
        self.current_iteration = iteration
        logger.debug(f"更新当前迭代号为: {iteration}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        if not self.thoughts:
            return {"total": 0}
        
        stats = {
            "total": len(self.thoughts),
            "by_type": {},
            "by_iteration": {},
            "session_id": self.session_id,
            "first_timestamp": min(t["timestamp"] for t in self.thoughts),
            "last_timestamp": max(t["timestamp"] for t in self.thoughts),
        }
        
        # 按类型统计
        for thought in self.thoughts:
            thought_type = thought["type"]
            stats["by_type"][thought_type] = stats["by_type"].get(thought_type, 0) + 1
            
            # 按迭代统计
            iteration = thought["iteration"]
            stats["by_iteration"][iteration] = stats["by_iteration"].get(iteration, 0) + 1
        
        return stats
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/thought_logging/test_recorder.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agent_with_backend/P1/thought_logging/recorder.py tests/thought_logging/test_recorder.py
git commit -m "feat: implement ThoughtRecorder core class"
```

---

### Task 4: OutputManager和文件写入器

**Files:**
- Create: `agent_with_backend/P1/thought_logging/output.py`
- Test: `tests/thought_logging/test_output.py`

- [ ] **Step 1: 编写OutputManager测试**

```python
# tests/thought_logging/test_output.py
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging.output import (
    OutputManager,
    JSONFileWriter,
    TextFileWriter,
    TerminalLogger
)
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_json_file_writer():
    """测试JSON文件写入器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = JSONFileWriter(temp_dir)
        
        # 测试写入单个记录
        thought = {
            "type": "test",
            "timestamp": 1234567890,
            "session_id": "test_session"
        }
        
        writer.write_thought(thought)
        
        # 验证文件存在
        session_dir = os.path.join(temp_dir, "test_session")
        json_file = os.path.join(session_dir, "thoughts.json")
        assert os.path.exists(json_file)
        
        # 验证JSON内容
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["type"] == "test"

def test_json_file_writer_append():
    """测试JSON文件追加写入"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = JSONFileWriter(temp_dir)
        
        # 写入第一条记录
        thought1 = {"type": "first", "id": 1}
        writer.write_thought(thought1)
        
        # 写入第二条记录
        thought2 = {"type": "second", "id": 2}
        writer.write_thought(thought2)
        
        # 验证两条记录都在文件中
        session_dir = os.path.join(temp_dir, thought1["session_id"])
        json_file = os.path.join(session_dir, "thoughts.json")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2

def test_text_file_writer():
    """测试文本文件写入器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = TextFileWriter(temp_dir)
        
        thought = {
            "type": "llm_call",
            "timestamp": 1234567890,
            "formatted_timestamp": "2026-04-17 09:44:11.858",
            "session_id": "test_session",
            "iteration": 1,
            "messages": [{"role": "user", "content": "测试"}],
            "response": {"content": "响应内容"}
        }
        
        writer.write_thought(thought)
        
        # 验证文件存在
        session_dir = os.path.join(temp_dir, "test_session")
        text_file = os.path.join(session_dir, "thoughts.log")
        assert os.path.exists(text_file)
        
        # 验证文本内容
        with open(text_file, 'r') as f:
            content = f.read()
            assert "LLM Call" in content
            assert "test_session" in content
            assert "迭代: 1" in content

def test_terminal_logger():
    """测试终端日志记录器"""
    with patch('builtins.print') as mock_print:
        logger = TerminalLogger(enabled=True)
        
        thought = {
            "type": "tool_decision",
            "tool_name": "query_drug",
            "iteration": 2
        }
        
        logger.log(thought)
        
        # 验证print被调用
        assert mock_print.called
        call_args = mock_print.call_args[0][0]
        assert "Tool Decision" in call_args
        assert "query_drug" in call_args

def test_output_manager():
    """测试OutputManager协调输出"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir
        )
        
        manager = OutputManager(config)
        
        # 验证组件已初始化
        assert manager.config == config
        assert manager.json_writer is not None
        assert manager.text_writer is not None
        assert manager.terminal_logger is not None
        assert manager.terminal_logger.enabled == False  # 配置中log_to_console=False
        
        # 测试写入思考记录
        thought = {
            "type": "llm_call",
            "session_id": "test_session"
        }
        
        # Mock各个写入器的write_thought方法
        with patch.object(manager.json_writer, 'write_thought') as mock_json, \
             patch.object(manager.text_writer, 'write_thought') as mock_text, \
             patch.object(manager.terminal_logger, 'log') as mock_terminal:
            
            manager.write_thought(thought)
            
            # 验证所有写入器都被调用
            mock_json.assert_called_once_with(thought)
            mock_text.assert_called_once_with(thought)
            mock_terminal.assert_not_called()  # 终端日志禁用

def test_output_manager_with_console():
    """测试启用终端输出的OutputManager"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=True,
            log_dir=temp_dir
        )
        
        manager = OutputManager(config)
        assert manager.terminal_logger.enabled == True
        
        thought = {"type": "test"}
        
        with patch.object(manager.json_writer, 'write_thought'), \
             patch.object(manager.text_writer, 'write_thought'), \
             patch.object(manager.terminal_logger, 'log') as mock_terminal:
            
            manager.write_thought(thought)
            mock_terminal.assert_called_once_with(thought)

def test_output_manager_file_only_formats():
    """测试仅文件格式的输出"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json"]  # 仅JSON格式
        )
        
        manager = OutputManager(config)
        
        thought = {"type": "test", "session_id": "test_session"}
        
        # 验证只有JSON写入器被初始化
        assert manager.json_writer is not None
        assert manager.text_writer is None  # text格式未启用
        
        # 写入应该只调用JSON写入器
        session_dir = os.path.join(temp_dir, "test_session")
        json_file = os.path.join(session_dir, "thoughts.json")
        
        # 确保文件不存在
        if os.path.exists(json_file):
            os.remove(json_file)
        
        manager.write_thought(thought)
        
        # 验证JSON文件已创建
        assert os.path.exists(json_file)
        
        # 验证没有text文件
        text_file = os.path.join(session_dir, "thoughts.log")
        assert not os.path.exists(text_file)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/thought_logging/test_output.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_with_backend.P1.thought_logging.output'"

- [ ] **Step 3: 实现OutputManager和文件写入器**

```python
# agent_with_backend/P1/thought_logging/output.py
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .config import ThoughtLoggingConfig
from .utils import safe_json_dumps, ensure_directory, format_timestamp

logger = logging.getLogger(__name__)

class JSONFileWriter:
    """JSON文件写入器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        logger.debug(f"JSONFileWriter初始化，基础目录: {base_dir}")
    
    def write_thought(self, thought: Dict[str, Any]) -> bool:
        """写入思考记录到JSON文件
        
        Args:
            thought: 思考记录
            
        Returns:
            是否成功
        """
        try:
            session_id = thought.get("session_id", "unknown_session")
            session_dir = os.path.join(self.base_dir, "sessions", session_id)
            
            if not ensure_directory(session_dir):
                return False
            
            json_file = os.path.join(session_dir, "thoughts.json")
            
            # 读取现有数据或创建新列表
            existing_data = []
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"读取JSON文件失败，创建新文件: {e}")
                    existing_data = []
            
            # 追加新记录
            existing_data.append(thought)
            
            # 写入文件
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"JSON记录已写入: {json_file}")
            return True
            
        except Exception as e:
            logger.error(f"写入JSON文件失败: {e}", exc_info=True)
            return False
    
    def write_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """写入会话元数据
        
        Args:
            session_id: 会话ID
            metadata: 元数据
            
        Returns:
            是否成功
        """
        try:
            session_dir = os.path.join(self.base_dir, "sessions", session_id)
            metadata_file = os.path.join(session_dir, "metadata.json")
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"元数据已写入: {metadata_file}")
            return True
            
        except Exception as e:
            logger.error(f"写入元数据失败: {e}", exc_info=True)
            return False

class TextFileWriter:
    """文本文件写入器（人类可读格式）"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        logger.debug(f"TextFileWriter初始化，基础目录: {base_dir}")
    
    def write_thought(self, thought: Dict[str, Any]) -> bool:
        """写入思考记录到文本文件
        
        Args:
            thought: 思考记录
            
        Returns:
            是否成功
        """
        try:
            session_id = thought.get("session_id", "unknown_session")
            session_dir = os.path.join(self.base_dir, "sessions", session_id)
            
            if not ensure_directory(session_dir):
                return False
            
            text_file = os.path.join(session_dir, "thoughts.log")
            
            # 格式化文本
            formatted_text = self._format_thought(thought)
            
            # 追加到文件
            with open(text_file, 'a', encoding='utf-8') as f:
                f.write(formatted_text + "\n\n")
            
            logger.debug(f"文本记录已写入: {text_file}")
            return True
            
        except Exception as e:
            logger.error(f"写入文本文件失败: {e}", exc_info=True)
            return False
    
    def _format_thought(self, thought: Dict[str, Any]) -> str:
        """格式化思考记录为人类可读文本
        
        Args:
            thought: 思考记录
            
        Returns:
            格式化文本
        """
        lines = []
        
        # 头部
        thought_type = thought.get("type", "unknown").upper().replace("_", " ")
        timestamp = thought.get("formatted_timestamp", format_timestamp())
        session_id = thought.get("session_id", "unknown")
        iteration = thought.get("iteration", "N/A")
        
        header = f"[THINKING] {thought_type}"
        separator = "─" * 80
        
        lines.append(separator)
        lines.append(header)
        lines.append(f"会话: {session_id} | 迭代: {iteration} | 时间: {timestamp}")
        lines.append(separator)
        
        # 根据类型格式化内容
        thought_type = thought.get("type")
        
        if thought_type == "llm_call":
            lines.extend(self._format_llm_call(thought))
        elif thought_type == "tool_decision":
            lines.extend(self._format_tool_decision(thought))
        elif thought_type == "iteration_state":
            lines.extend(self._format_iteration_state(thought))
        else:
            lines.append(f"未知类型: {thought_type}")
            lines.append(json.dumps(thought, ensure_ascii=False, indent=2))
        
        lines.append(separator)
        return "\n".join(lines)
    
    def _format_llm_call(self, thought: Dict[str, Any]) -> list:
        """格式化LLM调用记录"""
        lines = []
        
        # 元数据
        metadata = thought.get("metadata", {})
        if metadata:
            lines.append("元数据:")
            for key, value in metadata.items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
        
        # 消息
        messages = thought.get("messages", [])
        if messages:
            lines.append("消息:")
            for msg in messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                # 截断过长的内容
                if len(content) > 200:
                    content = content[:197] + "..."
                lines.append(f"  {role}: {content}")
            lines.append("")
        
        # 响应
        response = thought.get("response", {})
        content = response.get("content", "")
        if content:
            lines.append("响应:")
            lines.append(f"  {content}")
        
        # 工具调用
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            lines.append("")
            lines.append("工具调用:")
            for tool in tool_calls:
                name = tool.get("name", "unknown")
                inputs = tool.get("input", {})
                lines.append(f"  - {name}: {inputs}")
        
        return lines
    
    def _format_tool_decision(self, thought: Dict[str, Any]) -> list:
        """格式化工具调用决策记录"""
        lines = []
        
        tool_name = thought.get("tool_name", "unknown")
        reasoning = thought.get("reasoning")
        input_data = thought.get("input", {})
        result = thought.get("result", {})
        
        lines.append(f"工具: {tool_name}")
        lines.append("")
        
        if reasoning:
            lines.append("调用理由:")
            lines.append(f"  {reasoning}")
            lines.append("")
        
        if input_data:
            lines.append("输入参数:")
            lines.append(f"  {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            lines.append("")
        
        if result:
            lines.append("执行结果:")
            lines.append(f"  {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return lines
    
    def _format_iteration_state(self, thought: Dict[str, Any]) -> list:
        """格式化迭代状态记录"""
        lines = []
        
        state = thought.get("state", {})
        if state:
            lines.append("状态信息:")
            for key, value in state.items():
                if isinstance(value, dict) or isinstance(value, list):
                    lines.append(f"  - {key}:")
                    lines.append(f"    {json.dumps(value, ensure_ascii=False, indent=2)}")
                else:
                    lines.append(f"  - {key}: {value}")
        else:
            lines.append("无状态信息")
        
        return lines

class TerminalLogger:
    """终端日志记录器（实时输出）"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        logger.debug(f"TerminalLogger初始化，启用: {enabled}")
    
    def log(self, thought: Dict[str, Any]) -> None:
        """输出思考记录到终端
        
        Args:
            thought: 思考记录
        """
        if not self.enabled:
            return
        
        try:
            # 使用TextFileWriter的格式化方法
            writer = TextFileWriter("")  # 不需要实际目录
            formatted = writer._format_thought(thought)
            print(formatted)
            
        except Exception as e:
            logger.error(f"终端输出失败: {e}", exc_info=True)

class OutputManager:
    """输出管理器，协调不同格式的输出"""
    
    def __init__(self, config: ThoughtLoggingConfig):
        self.config = config
        
        # 初始化文件写入器
        self.json_writer = None
        self.text_writer = None
        
        if config.log_to_file:
            if "json" in config.log_formats:
                self.json_writer = JSONFileWriter(config.log_dir)
            if "text" in config.log_formats:
                self.text_writer = TextFileWriter(config.log_dir)
        
        # 初始化终端日志记录器
        self.terminal_logger = TerminalLogger(config.log_to_console)
        
        logger.debug(f"OutputManager初始化，配置: {config.to_dict()}")
    
    def write_thought(self, thought: Dict[str, Any]) -> None:
        """写入思考记录到所有启用的输出目标
        
        Args:
            thought: 思考记录
        """
        try:
            # 写入JSON文件
            if self.json_writer:
                self.json_writer.write_thought(thought)
            
            # 写入文本文件
            if self.text_writer:
                self.text_writer.write_thought(thought)
            
            # 输出到终端
            if self.terminal_logger:
                self.terminal_logger.log(thought)
                
        except Exception as e:
            logger.error(f"输出思考记录失败: {e}", exc_info=True)
    
    def write_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """写入会话元数据
        
        Args:
            session_id: 会话ID
            metadata: 元数据
        """
        try:
            if self.json_writer:
                self.json_writer.write_metadata(session_id, metadata)
        except Exception as e:
            logger.error(f"写入会话元数据失败: {e}", exc_info=True)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/thought_logging/test_output.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agent_with_backend/P1/thought_logging/output.py tests/thought_logging/test_output.py
git commit -m "feat: implement OutputManager and file writers"
```

---

### Task 5: 装饰器实现

**Files:**
- Create: `agent_with_backend/P1/thought_logging/decorators.py`
- Test: `tests/thought_logging/test_decorators.py`

- [ ] **Step 1: 编写装饰器测试**

```python
# tests/thought_logging/test_decorators.py
import functools
from unittest.mock import Mock, patch, MagicMock
from agent_with_backend.P1.thought_logging.decorators import (
    with_thought_logging,
    ThoughtLoggingDecorator,
    record_llm_calls,
    record_tool_decisions
)
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig
from agent_with_backend.P1.thought_logging.recorder import ThoughtRecorder

def test_with_thought_logging_decorator():
    """测试with_thought_logging装饰器"""
    # 创建一个模拟的Agent类
    class MockAgent:
        def __init__(self):
            self.value = "original"
        
        def run(self, message):
            return f"Processed: {message}"
    
    # 创建装饰后的Agent
    config = ThoughtLoggingConfig(enabled=True)
    decorated_agent = with_thought_logging(MockAgent(), config)
    
    # 验证装饰器添加了_recorder属性
    assert hasattr(decorated_agent, '_recorder')
    assert isinstance(decorated_agent._recorder, ThoughtRecorder)
    assert decorated_agent._recorder.enabled == True
    
    # 验证原始方法仍然可用
    assert decorated_agent.value == "original"
    result = decorated_agent.run("test message")
    assert result == "Processed: test message"

def test_thought_logging_decorator_class():
    """测试ThoughtLoggingDecorator类"""
    # 创建被装饰的类
    class TestClass:
        def __init__(self, name):
            self.name = name
        
        def method1(self, arg):
            return f"{self.name}: {arg}"
        
        def method2(self, a, b):
            return a + b
    
    # 创建装饰器配置
    config = ThoughtLoggingConfig(enabled=True)
    decorator = ThoughtLoggingDecorator(config)
    
    # 装饰类
    DecoratedClass = decorator.decorate_class(TestClass)
    
    # 创建实例
    instance = DecoratedClass("test")
    
    # 验证装饰器添加了_recorder属性
    assert hasattr(instance, '_recorder')
    assert instance._recorder.enabled == True
    
    # 验证原始方法仍然可用
    assert instance.name == "test"
    assert instance.method1("hello") == "test: hello"
    assert instance.method2(2, 3) == 5

def test_record_llm_calls_decorator():
    """测试record_llm_calls装饰器"""
    # 创建模拟的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True
    
    # 创建被装饰的函数
    @record_llm_calls(mock_recorder)
    def llm_chat(messages, **kwargs):
        return {
            "content": "Test response",
            "tool_calls": []
        }
    
    # 调用函数
    messages = [{"role": "user", "content": "test"}]
    result = llm_chat(messages, model="claude", temperature=0.5)
    
    # 验证结果
    assert result["content"] == "Test response"
    
    # 验证recorder被调用
    assert mock_recorder.record_llm_call.called
    call_args = mock_recorder.record_llm_call.call_args
    
    # 验证参数
    assert call_args[0][0] is None  # iteration=None
    assert call_args[0][1] == messages
    assert call_args[0][2]["content"] == "Test response"
    assert call_args[0][3]["model"] == "claude"
    assert call_args[0][3]["temperature"] == 0.5

def test_record_llm_calls_disabled():
    """测试禁用的record_llm_calls装饰器"""
    # 创建禁用的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = False
    
    @record_llm_calls(mock_recorder)
    def llm_chat(messages):
        return {"content": "response"}
    
    # 调用函数
    result = llm_chat([])
    
    # 验证结果
    assert result["content"] == "response"
    
    # 验证recorder未被调用（因为禁用）
    assert not mock_recorder.record_llm_call.called

def test_record_tool_decisions_decorator():
    """测试record_tool_decisions装饰器"""
    # 创建模拟的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True
    
    # 创建被装饰的函数
    @record_tool_decisions(mock_recorder)
    def execute_tool(tool_name, tool_input, **kwargs):
        return {"success": True, "result": "tool result"}
    
    # 调用函数
    tool_name = "query_drug"
    tool_input = {"症状": "头疼"}
    reasoning = "根据症状查询药物"
    
    result = execute_tool(
        tool_name, 
        tool_input, 
        reasoning=reasoning,
        iteration=2
    )
    
    # 验证结果
    assert result["success"] == True
    
    # 验证recorder被调用
    assert mock_recorder.record_tool_decision.called
    call_args = mock_recorder.record_tool_decision.call_args
    
    # 验证参数
    assert call_args[0][0] == 2  # iteration=2
    assert call_args[0][1] == tool_name
    assert call_args[0][2] == tool_input
    assert call_args[0][3] == reasoning
    assert call_args[0][4]["success"] == True

def test_decorator_preserves_metadata():
    """测试装饰器保留函数元数据"""
    def original_func(arg1, arg2=None):
        """原始函数的文档字符串"""
        return arg1 + (arg2 or 0)
    
    original_func.custom_attr = "custom_value"
    
    # 装饰函数
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True
    
    decorated_func = record_llm_calls(mock_recorder)(original_func)
    
    # 验证元数据被保留
    assert decorated_func.__name__ == "original_func"
    assert decorated_func.__doc__ == "原始函数的文档字符串"
    assert decorated_func.custom_attr == "custom_value"
    
    # 验证签名被保留
    import inspect
    sig = inspect.signature(decorated_func)
    params = list(sig.parameters.keys())
    assert params == ["arg1", "arg2"]

def test_decorator_error_handling():
    """测试装饰器错误处理"""
    # 创建会抛出异常的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True
    mock_recorder.record_llm_call.side_effect = Exception("Recorder error")
    
    @record_llm_calls(mock_recorder)
    def llm_chat(messages):
        return {"content": "response"}
    
    # 调用应该成功，即使recorder出错
    result = llm_chat([])
    assert result["content"] == "response"
    
    # 验证recorder被调用（虽然出错了）
    assert mock_recorder.record_llm_call.called
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/thought_logging/test_decorators.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_with_backend.P1.thought_logging.decorators'"

- [ ] **Step 3: 实现装饰器**

```python
# agent_with_backend/P1/thought_logging/decorators.py
import functools
import logging
from typing import Callable, Any, Optional
from inspect import signature

from .config import ThoughtLoggingConfig
from .recorder import ThoughtRecorder
from .output import OutputManager

logger = logging.getLogger(__name__)

def record_llm_calls(recorder: ThoughtRecorder):
    """装饰器：记录LLM调用
    
    Args:
        recorder: ThoughtRecorder实例
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        """实际装饰器"""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """包装函数"""
            
            # 执行前：准备记录数据
            iteration = kwargs.get('iteration')
            metadata = {
                'function_name': func.__name__,
                'args': args,
                'kwargs': {k: v for k, v in kwargs.items() if k != 'iteration'}
            }
            
            try:
                # 执行原始函数
                result = func(*args, **kwargs)
                
                # 执行后：记录LLM调用
                if recorder.enabled:
                    try:
                        # 提取消息和响应
                        # 假设第一个位置参数是messages，或者有关键字参数messages
                        messages = None
                        if args and isinstance(args[0], list):
                            messages = args[0]
                        elif 'messages' in kwargs:
                            messages = kwargs['messages']
                        
                        if messages is not None:
                            recorder.record_llm_call(
                                iteration=iteration,
                                messages=messages,
                                response=result,
                                metadata=metadata
                            )
                    except Exception as e:
                        logger.error(f"记录LLM调用失败: {e}", exc_info=True)
                        # 不重新抛出异常，避免影响主流程
                
                return result
                
            except Exception as e:
                # 记录错误
                if recorder.enabled:
                    try:
                        error_metadata = metadata.copy()
                        error_metadata['error'] = str(e)
                        recorder.record_llm_call(
                            iteration=iteration,
                            messages=[],
                            response={"error": str(e)},
                            metadata=error_metadata
                        )
                    except Exception as record_error:
                        logger.error(f"记录错误失败: {record_error}", exc_info=True)
                
                # 重新抛出原始异常
                raise
        
        return wrapper
    
    return decorator

def record_tool_decisions(recorder: ThoughtRecorder):
    """装饰器：记录工具调用决策
    
    Args:
        recorder: ThoughtRecorder实例
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        """实际装饰器"""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """包装函数"""
            
            # 提取参数
            tool_name = None
            tool_input = None
            reasoning = kwargs.get('reasoning')
            iteration = kwargs.get('iteration')
            
            # 根据参数位置或名称提取
            if args:
                if len(args) >= 1:
                    tool_name = args[0]
                if len(args) >= 2:
                    tool_input = args[1]
            else:
                tool_name = kwargs.get('tool_name')
                tool_input = kwargs.get('tool_input')
            
            try:
                # 执行原始函数
                result = func(*args, **kwargs)
                
                # 执行后：记录工具调用决策
                if recorder.enabled and tool_name is not None:
                    try:
                        recorder.record_tool_decision(
                            iteration=iteration,
                            tool_name=tool_name,
                            input_data=tool_input or {},
                            reasoning=reasoning,
                            result=result
                        )
                    except Exception as e:
                        logger.error(f"记录工具调用决策失败: {e}", exc_info=True)
                        # 不重新抛出异常，避免影响主流程
                
                return result
                
            except Exception as e:
                # 记录错误
                if recorder.enabled and tool_name is not None:
                    try:
                        recorder.record_tool_decision(
                            iteration=iteration,
                            tool_name=tool_name,
                            input_data=tool_input or {},
                            reasoning=reasoning,
                            result={"error": str(e)}
                        )
                    except Exception as record_error:
                        logger.error(f"记录工具错误失败: {record_error}", exc_info=True)
                
                # 重新抛出原始异常
                raise
        
        return wrapper
    
    return decorator

class ThoughtLoggingDecorator:
    """思考记录装饰器类"""
    
    def __init__(self, config: ThoughtLoggingConfig):
        self.config = config
        self.recorder = ThoughtRecorder(config)
        self.output_manager = OutputManager(config)
        
        # 连接recorder和output_manager
        self._connect_recorder_to_output()
        
        logger.debug(f"ThoughtLoggingDecorator初始化")
    
    def _connect_recorder_to_output(self):
        """连接recorder到output_manager"""
        # 创建一个包装recorder的方法，在记录时同时输出
        original_record_methods = {
            'record_llm_call': self.recorder.record_llm_call,
            'record_tool_decision': self.recorder.record_tool_decision,
            'record_iteration_state': self.recorder.record_iteration_state,
        }
        
        def make_wrapped_method(method_name, original_method):
            def wrapped_method(*args, **kwargs):
                # 调用原始方法
                result = original_method(*args, **kwargs)
                
                # 获取最新记录并输出
                if self.recorder.thoughts:
                    latest_thought = self.recorder.thoughts[-1]
                    self.output_manager.write_thought(latest_thought)
                
                return result
            
            return wrapped_method
        
        # 替换recorder的方法
        for method_name, original_method in original_record_methods.items():
            wrapped_method = make_wrapped_method(method_name, original_method)
            setattr(self.recorder, method_name, wrapped_method)
    
    def decorate_class(self, cls):
        """装饰一个类，为其添加思考记录功能
        
        Args:
            cls: 要装饰的类
            
        Returns:
            装饰后的类
        """
        # 保存原始__init__
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # 调用原始__init__
            original_init(self, *args, **kwargs)
            
            # 添加recorder属性
            self._recorder = self.recorder
            
            # 装饰特定方法
            self._decorate_methods()
        
        # 替换__init__
        cls.__init__ = new_init
        
        # 添加装饰器属性
        cls.recorder = self.recorder
        cls.output_manager = self.output_manager
        cls._decorate_methods = lambda self: self._decorate_instance_methods()
        
        # 为实例添加方法装饰逻辑
        def _decorate_instance_methods(self):
            """装饰实例方法"""
            # 这里可以根据需要装饰特定方法
            # 例如：如果类有chat方法，用record_llm_calls装饰
            if hasattr(self, 'chat'):
                self.chat = record_llm_calls(self._recorder)(self.chat)
            
            # 如果类有run方法，记录迭代状态
            if hasattr(self, 'run'):
                original_run = self.run
                
                @functools.wraps(original_run)
                def wrapped_run(*args, **kwargs):
                    # 记录迭代开始
                    if self._recorder.enabled:
                        self._recorder.record_iteration_state(
                            iteration=self._recorder.current_iteration,
                            state={"method": "run", "args": args, "kwargs": kwargs}
                        )
                    
                    # 执行原始方法
                    result = original_run(*args, **kwargs)
                    
                    # 更新迭代计数器
                    if self._recorder.enabled:
                        self._recorder.update_iteration(self._recorder.current_iteration + 1)
                    
                    return result
                
                self.run = wrapped_run
        
        cls._decorate_instance_methods = _decorate_instance_methods
        
        return cls

def with_thought_logging(obj, config: Optional[ThoughtLoggingConfig] = None):
    """为对象添加思考记录功能
    
    Args:
        obj: 要装饰的对象（类或实例）
        config: 配置对象，如果为None则使用默认配置
        
    Returns:
        装饰后的对象
    """
    if config is None:
        config = ThoughtLoggingConfig()
    
    decorator = ThoughtLoggingDecorator(config)
    
    if isinstance(obj, type):
        # 装饰类
        return decorator.decorate_class(obj)
    else:
        # 装饰实例
        # 添加recorder属性
        obj._recorder = decorator.recorder
        obj._output_manager = decorator.output_manager
        
        # 装饰实例方法
        if hasattr(obj, 'chat'):
            obj.chat = record_llm_calls(obj._recorder)(obj.chat)
        
        if hasattr(obj, 'run'):
            original_run = obj.run
            
            @functools.wraps(original_run)
            def wrapped_run(*args, **kwargs):
                # 记录迭代开始
                if obj._recorder.enabled:
                    obj._recorder.record_iteration_state(
                        iteration=obj._recorder.current_iteration,
                        state={"method": "run", "args": args, "kwargs": kwargs}
                    )
                
                # 执行原始方法
                result = original_run(*args, **kwargs)
                
                # 更新迭代计数器
                if obj._recorder.enabled:
                    obj._recorder.update_iteration(obj._recorder.current_iteration + 1)
                
                return result
            
            obj.run = wrapped_run
        
        return obj
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/thought_logging/test_decorators.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agent_with_backend/P1/thought_logging/decorators.py tests/thought_logging/test_decorators.py
git commit -m "feat: implement thought logging decorators"
```

---

### Task 6: 与MedicalAgent集成

**Files:**
- Modify: `agent_with_backend/P1/cli/interactive.py:24-110`
- Create: `agent_with_backend/P1/thought_logging/__init__.py` (完善)
- Test: `tests/thought_logging/test_integration.py`

- [ ] **Step 1: 完善包初始化文件**

```python
# agent_with_backend/P1/thought_logging/__init__.py
"""
思考记录模块

为医疗助手Agent添加LLM思考过程记录功能，支持详细级别的思考过程记录、
双格式日志输出和可选调试模式。
"""

from .config import ThoughtLoggingConfig
from .recorder import ThoughtRecorder
from .output import OutputManager, JSONFileWriter, TextFileWriter, TerminalLogger
from .decorators import (
    with_thought_logging,
    ThoughtLoggingDecorator,
    record_llm_calls,
    record_tool_decisions
)
from .utils import (
    generate_session_id,
    format_timestamp,
    safe_json_dumps,
    ensure_directory,
    get_current_time_ms,
    sanitize_for_logging
)

__version__ = "1.0.0"
__all__ = [
    # 配置
    "ThoughtLoggingConfig",
    
    # 核心类
    "ThoughtRecorder",
    "OutputManager",
    "JSONFileWriter",
    "TextFileWriter",
    "TerminalLogger",
    
    # 装饰器
    "with_thought_logging",
    "ThoughtLoggingDecorator",
    "record_llm_calls",
    "record_tool_decisions",
    
    # 工具函数
    "generate_session_id",
    "format_timestamp",
    "safe_json_dumps",
    "ensure_directory",
    "get_current_time_ms",
    "sanitize_for_logging",
]
```

- [ ] **Step 2: 编写集成测试**

```python
# tests/thought_logging/test_integration.py
import os
import tempfile
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging import with_thought_logging
from agent_with_backend.P1.core.agent import MedicalAgent
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_integration_with_medical_agent():
    """测试与MedicalAgent的集成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json", "text"]
        )
        
        # 创建MedicalAgent（模拟）
        class MockLLMClient:
            def chat(self, messages, tools=None, temperature=None):
                return {
                    "content": "调用 query_drug(症状='头疼')",
                    "tool_calls": [{"name": "query_drug", "input": {"症状": "头疼"}}]
                }
        
        # 使用patch模拟MedicalAgent的依赖
        with patch('agent_with_backend.P1.core.agent.LLMClient', MockLLMClient):
            # 创建原始Agent
            original_agent = MedicalAgent()
            
            # 使用思考记录装饰器
            decorated_agent = with_thought_logging(original_agent, config)
            
            # 验证装饰器添加了属性
            assert hasattr(decorated_agent, '_recorder')
            assert hasattr(decorated_agent, '_output_manager')
            assert decorated_agent._recorder.enabled == True
            
            # 验证原始方法仍然可用
            assert hasattr(decorated_agent, 'run')
            assert hasattr(decorated_agent, 'reset')
            assert hasattr(decorated_agent, 'get_approval_id')
            
            # 验证run方法被装饰
            # 注意：由于Mock，我们无法实际运行run方法，但可以验证属性存在

def test_integration_disabled():
    """测试禁用状态的集成"""
    # 创建禁用配置
    config = ThoughtLoggingConfig(enabled=False)
    
    # 创建原始Agent
    original_agent = MedicalAgent()
    
    # 使用思考记录装饰器
    decorated_agent = with_thought_logging(original_agent, config)
    
    # 验证装饰器添加了属性（即使禁用）
    assert hasattr(decorated_agent, '_recorder')
    assert decorated_agent._recorder.enabled == False

def test_integration_cli_compatibility():
    """测试CLI兼容性"""
    # 验证思考记录模块不会破坏现有CLI接口
    from agent_with_backend.P1.cli.interactive import simple_interactive_mode
    
    # 使用patch模拟用户输入和Agent运行
    with patch('builtins.input', side_effect=["/exit"]), \
         patch('agent_with_backend.P1.cli.interactive.MedicalAgent') as MockAgent, \
         patch('agent_with_backend.P1.cli.interactive.with_thought_logging') as mock_decorator:
        
        # 配置模拟
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = ("响应内容", [])
        MockAgent.return_value = mock_agent_instance
        
        # 模拟装饰器返回原对象
        mock_decorator.side_effect = lambda x, config=None: x
        
        # 运行CLI函数（应该正常退出）
        try:
            simple_interactive_mode()
            # 如果到达这里，说明没有异常
            assert True
        except Exception as e:
            # 不应该有异常
            assert False, f"CLI函数抛出异常: {e}"

def test_log_file_generation():
    """测试日志文件生成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json", "text"]
        )
        
        # 创建装饰器
        from agent_with_backend.P1.thought_logging import ThoughtLoggingDecorator
        decorator = ThoughtLoggingDecorator(config)
        
        # 模拟一个类
        class TestAgent:
            def run(self, message):
                # 模拟LLM调用
                self._recorder.record_llm_call(
                    iteration=0,
                    messages=[{"role": "user", "content": message}],
                    response={"content": "响应"},
                    metadata={"provider": "test"}
                )
                return "结果"
        
        # 装饰类
        DecoratedAgent = decorator.decorate_class(TestAgent)
        
        # 创建实例
        agent = DecoratedAgent()
        
        # 运行方法
        result = agent.run("测试消息")
        assert result == "结果"
        
        # 验证日志文件生成
        session_id = agent._recorder.session_id
        session_dir = os.path.join(temp_dir, "sessions", session_id)
        
        assert os.path.exists(session_dir)
        assert os.path.exists(os.path.join(session_dir, "thoughts.json"))
        assert os.path.exists(os.path.join(session_dir, "thoughts.log"))
```

- [ ] **Step 3: 运行集成测试验证失败**

Run: `pytest tests/thought_logging/test_integration.py -v`
Expected: FAIL (部分测试可能失败，因为需要实际集成)

- [ ] **Step 4: 修改CLI以集成思考记录**

```python
# agent_with_backend/P1/cli/interactive.py:24-110
# 修改simple_interactive_mode函数

def simple_interactive_mode(patient_id: Optional[str] = None):
    """简单交互模式"""
    print("\n" + "=" * 60)
    print("P1医疗用药助手 - 简单交互模式")
    print("=" * 60)
    print("输入您的症状或问题，Agent会进行处理")
    print("输入 '/reset' 重置对话")
    print("输入 '/exit' 或按 Ctrl+C 退出")
    
    # 显示思考记录状态
    from ..core.config import Config
    if Config.ENABLE_THOUGHT_LOGGING:
        print("思考记录: 已启用")
        print(f"日志目录: {Config.THOUGHT_LOG_DIR}")
    else:
        print("思考记录: 已禁用")
    
    print("=" * 60)

    try:
        from ..core.agent import MedicalAgent
        from ..thought_logging import with_thought_logging
        
        # 创建配置
        from ..thought_logging.config import ThoughtLoggingConfig
        thought_config = ThoughtLoggingConfig()
        
        # 创建Agent
        base_agent = MedicalAgent()
        
        # 根据配置决定是否启用思考记录
        if thought_config.enabled:
            agent = with_thought_logging(base_agent, thought_config)
            print(f"\n思考记录已启用，会话ID: {agent._recorder.session_id}")
        else:
            agent = base_agent
            print("\n思考记录已禁用")
        
        current_patient_id = patient_id or "default_patient"
        print(f"\n患者ID: {current_patient_id}")
        print("MedicalAgent已初始化，开始对话...\n")

        while True:
            try:
                # 获取用户输入
                user_input = input("您: ").strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.lower() == "/exit":
                    print("\n退出程序...")
                    break
                elif user_input.lower() == "/reset":
                    agent.reset()
                    print("对话已重置")
                    
                    # 如果启用了思考记录，也重置记录器
                    if hasattr(agent, '_recorder') and agent._recorder.enabled:
                        agent._recorder.clear_thoughts()
                        agent._recorder.update_iteration(0)
                        print("思考记录已重置")
                    
                    continue
                elif user_input.lower() == "/help":
                    print("\n可用命令:")
                    print("  /reset  - 重置对话")
                    print("  /exit   - 退出程序")
                    print("  /help   - 显示帮助")
                    if hasattr(agent, '_recorder') and agent._recorder.enabled:
                        print("  /thoughts - 显示思考记录统计")
                    print("\n直接输入您的症状或问题进行咨询")
                    continue
                elif user_input.lower() == "/thoughts":
                    if hasattr(agent, '_recorder') and agent._recorder.enabled:
                        stats = agent._recorder.get_stats()
                        print("\n思考记录统计:")
                        print(f"  总记录数: {stats['total']}")
                        print(f"  会话ID: {stats['session_id']}")
                        if 'by_type' in stats:
                            print("  按类型统计:")
                            for ttype, count in stats['by_type'].items():
                                print(f"    - {ttype}: {count}")
                    else:
                        print("\n思考记录未启用")
                    continue
                elif user_input.startswith("/"):
                    print(f"未知命令: {user_input}")
                    print("输入 '/help' 查看可用命令")
                    continue

                # 处理医疗咨询
                print("\n[处理中...]", end="", flush=True)

                try:
                    response, steps = agent.run(
                        user_input, patient_id=current_patient_id
                    )

                    # 显示响应
                    print("\n助手:", response)

                    # 显示统计信息
                    tool_calls = len([s for s in steps if s.get("type") == "tool_call"])
                    if tool_calls > 0:
                        print(f"[本次使用了 {tool_calls} 个工具调用]")
                    
                    # 如果启用了思考记录，显示简要统计
                    if hasattr(agent, '_recorder') and agent._recorder.enabled:
                        stats = agent._recorder.get_stats()
                        print(f"[思考记录: {stats['total']} 条记录]")

                except Exception as e:
                    print(f"\n处理失败: {e}")

                print()  # 空行

            except KeyboardInterrupt:
                print("\n\n检测到Ctrl+C，退出程序...")
                break
            except EOFError:
                print("\n\n检测到EOF，退出程序...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                continue

    except ImportError as e:
        print(f"导入失败: {e}")
        print("请确保已安装所有依赖：pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)
```

- [ ] **Step 5: 运行集成测试验证通过**

Run: `pytest tests/thought_logging/test_integration.py -v`
Expected: PASS（可能需要调整mock）

- [ ] **Step 6: 运行现有CLI测试确保兼容性**

Run: `pytest agent_with_backend/P1/tests/ -k cli -v`
Expected: PASS（现有测试应继续通过）

- [ ] **Step 7: 提交**

```bash
git add agent_with_backend/P1/thought_logging/__init__.py agent_with_backend/P1/cli/interactive.py tests/thought_logging/test_integration.py
git commit -m "feat: integrate thought logging with MedicalAgent and CLI"
```

---

### Task 7: 创建使用说明文档

**Files:**
- Create: `docs/thought_logging_usage.md`
- Create: `.thought_logging.env.example`

- [ ] **Step 1: 创建使用说明文档**

```markdown
# LLM思考记录系统使用说明

## 概述

LLM思考记录系统为医疗助手Agent添加了完整的思考过程记录功能，能够捕获LLM的响应内容、工具调用决策逻辑和迭代状态，并以两种格式（JSON和文本）输出到日志文件夹中。

## 快速开始

### 1. 启用思考记录

设置环境变量启用思考记录：

```bash
export ENABLE_THOUGHT_LOGGING=true
export THOUGHT_LOG_DIR=./logs/thoughts
```

### 2. 运行CLI

使用现有CLI接口，功能会自动启用：

```bash
python interactive.py
```

### 3. 查看日志

日志文件会自动生成在指定目录：

```bash
# 查看最新的会话日志
ls -la ./logs/thoughts/sessions/
tail -f ./logs/thoughts/sessions/latest/thoughts.log
```

## 配置选项

### 基础配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `ENABLE_THOUGHT_LOGGING` | `false` | 启用/禁用思考记录 |
| `THOUGHT_LOG_LEVEL` | `DETAILED` | 日志级别：`BASIC`, `STANDARD`, `DETAILED`, `DEBUG` |
| `THOUGHT_LOG_TO_FILE` | `true` | 是否输出到文件 |
| `THOUGHT_LOG_TO_CONSOLE` | `false` | 是否输出到终端 |
| `THOUGHT_LOG_DIR` | `./logs/thoughts` | 日志目录 |

### 高级配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `THOUGHT_LOG_FORMATS` | `json,text` | 日志格式，逗号分隔：`json`, `text` |
| `THOUGHT_SESSION_AUTO_CLEANUP` | `true` | 自动清理旧会话 |
| `THOUGHT_SESSION_RETENTION_DAYS` | `7` | 会话保留天数 |

### 配置文件示例

创建 `.thought_logging.env` 文件：

```bash
# 思考记录配置
ENABLE_THOUGHT_LOGGING=true
THOUGHT_LOG_LEVEL=DETAILED
THOUGHT_LOG_TO_FILE=true
THOUGHT_LOG_TO_CONSOLE=false
THOUGHT_LOG_DIR=./logs/thoughts
THOUGHT_LOG_FORMATS=json,text
THOUGHT_SESSION_AUTO_CLEANUP=true
THOUGHT_SESSION_RETENTION_DAYS=7
```

然后加载配置：

```bash
export $(cat .thought_logging.env | xargs)
```

## CLI使用

### 现有命令

所有现有CLI命令保持不变：

```bash
# 交互模式
python interactive.py [患者ID]

# 带详细输出
python interactive.py --verbose

# 指定患者
python interactive.py patient_123
```

### 新增命令

启用思考记录后，CLI会添加以下命令：

- `/thoughts` - 显示当前会话的思考记录统计
- 思考记录状态会在启动时显示

## 日志文件结构

```
logs/thoughts/
├── sessions/                    # 按会话组织的日志
│   ├── session_20260417_094411/
│   │   ├── thoughts.json       # 结构化JSON日志
│   │   ├── thoughts.log        # 人类可读文本日志
│   │   └── metadata.json       # 会话元数据
│   └── session_20260417_101522/
│       ├── thoughts.json
│       ├── thoughts.log
│       └── metadata.json
├── daily/                       # 按日期汇总（未来功能）
│   ├── 2026-04-17.json
│   └── 2026-04-17.log
└── index.json                   # 日志索引（未来功能）
```

### JSON格式示例

```json
{
  "session_id": "session_20260417_094411",
  "timestamp": 1713321851.858,
  "type": "llm_call",
  "iteration": 0,
  "messages": [...],
  "response": {...},
  "metadata": {...}
}
```

### 文本格式示例

```
──────────────────────────────────────────────────────────────────────────────
[THINKING] LLM CALL
──────────────────────────────────────────────────────────────────────────────
会话: session_20260417_094411 | 迭代: 0 | 时间: 2026-04-17 09:44:11.858
──────────────────────────────────────────────────────────────────────────────
元数据:
  - provider: claude
  - model: claude-3-sonnet-20240229

消息:
  SYSTEM: 你是医疗用药助手...
  USER: 老王,30岁,60kg,轻度头疼,无过敏历史

响应:
  调用 query_drug(症状="头疼")

工具调用:
  - query_drug: {"症状": "头疼"}
──────────────────────────────────────────────────────────────────────────────
```

## 程序化使用

### 直接使用思考记录模块

```python
from agent_with_backend.P1.thought_logging import (
    ThoughtLoggingConfig,
    ThoughtRecorder,
    with_thought_logging
)

# 创建配置
config = ThoughtLoggingConfig(enabled=True)

# 装饰现有对象
from agent_with_backend.P1.core.agent import MedicalAgent
agent = MedicalAgent()
agent_with_logging = with_thought_logging(agent, config)

# 使用装饰后的Agent
response, steps = agent_with_logging.run("患者症状描述")
```

### 手动记录

```python
from agent_with_backend.P1.thought_logging import ThoughtRecorder, ThoughtLoggingConfig

config = ThoughtLoggingConfig(enabled=True)
recorder = ThoughtRecorder(config)

# 记录LLM调用
recorder.record_llm_call(
    iteration=0,
    messages=[{"role": "user", "content": "症状"}],
    response={"content": "响应"},
    metadata={"provider": "claude"}
)

# 获取记录
thoughts = recorder.get_thoughts_by_type("llm_call")
stats = recorder.get_stats()
```

## 故障排除

### 常见问题

1. **日志文件未生成**
   - 检查 `ENABLE_THOUGHT_LOGGING` 是否设置为 `true`
   - 检查 `THOUGHT_LOG_TO_FILE` 是否设置为 `true`
   - 检查日志目录权限

2. **性能问题**
   - 如果对性能敏感，可以降低日志级别：`THOUGHT_LOG_LEVEL=BASIC`
   - 或禁用文件输出：`THOUGHT_LOG_TO_FILE=false`

3. **磁盘空间不足**
   - 启用自动清理：`THOUGHT_SESSION_AUTO_CLEANUP=true`
   - 减少保留天数：`THOUGHT_SESSION_RETENTION_DAYS=3`

### 调试

启用调试输出：

```bash
export THOUGHT_LOG_LEVEL=DEBUG
export THOUGHT_LOG_TO_CONSOLE=true
```

## API参考

详细API文档请参考源代码文档字符串。

---

**版本**: 1.0.0  
**最后更新**: 2026-04-17
```

- [ ] **Step 2: 创建环境变量示例文件**

```bash
# .thought_logging.env.example
# LLM思考记录系统配置示例
# 复制此文件为 .thought_logging.env 并修改配置

# 启用思考记录
ENABLE_THOUGHT_LOGGING=true

# 日志级别
THOUGHT_LOG_LEVEL=DETAILED  # BASIC, STANDARD, DETAILED, DEBUG

# 输出目标
THOUGHT_LOG_TO_FILE=true
THOUGHT_LOG_TO_CONSOLE=false

# 日志目录
THOUGHT_LOG_DIR=./logs/thoughts

# 日志格式（逗号分隔）
THOUGHT_LOG_FORMATS=json,text  # json, text

# 会话管理
THOUGHT_SESSION_AUTO_CLEANUP=true
THOUGHT_SESSION_RETENTION_DAYS=7

# 注意：思考记录会增加系统开销，生产环境建议谨慎启用
```

- [ ] **Step 3: 提交**

```bash
git add docs/thought_logging_usage.md .thought_logging.env.example
git commit -m "docs: add thought logging usage documentation"
```

---

### Task 8: 完整系统测试

**Files:**
- Test: 运行所有思考记录测试
- Test: 运行现有系统测试确保兼容性

- [ ] **Step 1: 运行所有思考记录测试**

```bash
pytest tests/thought_logging/ -v
```

Expected: 所有测试通过

- [ ] **Step 2: 运行现有系统测试确保兼容性**

```bash
pytest agent_with_backend/P1/tests/ -v
```

Expected: 所有现有测试通过（思考记录不应影响现有功能）

- [ ] **Step 3: 手动测试CLI集成**

```bash
# 测试1: 禁用思考记录（默认）
cd agent_with_backend/P1
python cli/interactive.py <<< "/exit"
```

Expected: 正常启动和退出，无错误

- [ ] **Step 4: 测试启用思考记录**

```bash
# 测试2: 启用思考记录
cd agent_with_backend/P1
ENABLE_THOUGHT_LOGGING=true THOUGHT_LOG_DIR=./test_logs python cli/interactive.py <<< "测试症状"
```

Expected: 
1. 正常启动，显示"思考记录: 已启用"
2. 处理用户输入
3. 生成日志文件
4. 正常退出

检查日志文件：
```bash
ls -la ./test_logs/sessions/
```

Expected: 会话目录和日志文件已创建

- [ ] **Step 5: 清理测试文件**

```bash
rm -rf ./test_logs
```

- [ ] **Step 6: 提交最终版本**

```bash
git add .
git commit -m "feat: complete thought logging system implementation"
```

---

## 计划完成状态

✅ **所有任务定义完成**

### 实施总结

本计划完整实现了LLM思考记录系统，包括：

1. ✅ **配置系统**：环境变量驱动的配置管理
2. ✅ **核心记录器**：ThoughtRecorder类，支持三种记录类型
3. ✅ **输出系统**：OutputManager协调JSON和文本格式输出
4. ✅ **装饰器模式**：非侵入式集成现有类
5. ✅ **CLI集成**：与现有interactive.py无缝集成
6. ✅ **文档**：完整的使用说明和示例
7. ✅ **测试**：完整的单元测试和集成测试

### 关键特性实现

- **非侵入式设计**：通过装饰器包装，不修改原始类
- **双格式日志**：JSON（程序分析）+ 文本（人工阅读）
- **详细级别记录**：完整的思考过程捕获
- **配置驱动**：所有功能通过环境变量控制
- **向后兼容**：现有CLI接口完全不变
- **错误恢复**：记录失败不影响主流程

### 下一步

计划已保存到 `docs/superpowers/plans/2026-04-17-llm-thought-logging-implementation.md`

**执行选项：**

1. **子代理驱动（推荐）** - 我分派独立子代理执行每个任务，任务间有审查
2. **内联执行** - 在当前会话中执行计划，分批执行并检查点

**请选择执行方式：**