---
name: LLM思考记录系统设计
description: 为医疗助手Agent添加LLM思考过程记录功能，支持详细级别的思考过程记录、双格式日志输出和可选调试模式
type: design
---

# LLM思考记录系统设计

## 概述

本设计旨在为ROS2智能取药系统的医疗助手Agent添加LLM思考过程记录功能。系统将捕获完整的LLM思考过程，包括响应内容、工具调用决策逻辑和迭代状态，并以两种格式（结构化JSON和人类可读文本）输出到独立的日志文件夹中。

## 设计决策

### 用户需求确认
1. **记录内容**：完整的LLM响应内容、工具调用的决策逻辑、每次迭代的完整状态、LLM的内部思考过程（如果支持）
2. **输出格式**：人类可读的日志文件 + 实时终端输出（文件日志优先）
3. **日志详细程度**：详细级别（完整思考过程）
4. **集成方式**：作为可选的调试模式，通过配置开关控制
5. **技术实现**：装饰器模式，最小化对现有代码的改动
6. **向后兼容**：必须保证现有CLI接口完全不变
7. **性能影响**：可以接受一定的性能开销

### 关键约束
- 不修改现有类的方法签名
- 不改变现有CLI接口
- 通过配置开关控制功能启用/禁用
- 创建独立的日志文件夹存储所有日志文件

## 架构设计

### 系统组件
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MedicalAgent  │    │    LLMClient    │    │   CLI/交互界面  │
│   (原有代码)    │    │   (原有代码)    │    │   (原有代码)    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ├──────────────────────┼──────────────────────┤
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│ AgentRecorder   │    │  LLMRecorder    │    │   ConfigLoader  │
│   (装饰器)      │    │   (装饰器)      │    │   (配置管理)    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────┬───────────┴──────────┬───────────┘
                    │                      │
           ┌────────▼────────┐    ┌────────▼────────┐
           │ ThoughtRecorder │    │   ThoughtLogger │
           │  (核心记录器)   │    │   (日志处理器)  │
           └────────┬────────┘    └────────┬────────┘
                    │                      │
           ┌────────▼──────────────────────▼────────┐
           │             OutputManager              │
           │           (输出管理器)                 │
           └────────┬──────────────────────┬────────┘
                    │                      │
          ┌─────────▼────────┐    ┌────────▼────────┐
          │  JSONFileWriter  │    │  TextFileWriter │
          │ (JSON文件写入器) │    │ (文本文件写入器)│
          └──────────────────┘    └─────────────────┘
```

### 数据流
1. **触发记录**：装饰器在方法调用前后触发记录事件
2. **数据收集**：ThoughtRecorder收集LLM调用、工具决策、迭代状态等数据
3. **格式处理**：OutputManager将数据转换为两种格式（JSON和文本）
4. **输出写入**：分别由JSONFileWriter和TextFileWriter写入文件
5. **实时显示**：ThoughtLogger同时输出到终端（可选）

## 组件设计

### 1. ThoughtRecorder（核心记录器）
```python
class ThoughtRecorder:
    """思考记录器核心类，负责收集和存储思考过程数据"""
    
    def __init__(self, enabled=False, log_level="DETAILED"):
        self.enabled = enabled
        self.log_level = log_level
        self.session_id = generate_session_id()
        self.thoughts = []  # 按时间顺序存储所有思考记录
        self.current_iteration = 0
        
    def record_llm_call(self, iteration, messages, response, metadata=None):
        """记录一次LLM调用"""
        if not self.enabled:
            return
        
        thought = {
            "type": "llm_call",
            "timestamp": time.time(),
            "session_id": self.session_id,
            "iteration": iteration,
            "messages": messages,  # 完整消息历史
            "response": response,  # 完整响应内容
            "tool_calls": response.get("tool_calls", []),
            "metadata": {
                "provider": metadata.get("provider"),
                "model": metadata.get("model"),
                "thinking_supported": metadata.get("thinking_supported", False),
                "thinking_content": metadata.get("thinking_content"),
                **metadata
            }
        }
        self.thoughts.append(thought)
        self._notify_output(thought)
    
    def record_tool_decision(self, iteration, tool_name, input_data, reasoning, result):
        """记录工具调用决策"""
        # 类似实现...
    
    def record_iteration_state(self, iteration, state):
        """记录迭代状态"""
        # 类似实现...
```

### 2. OutputManager（输出管理器）
```python
class OutputManager:
    """输出管理器，负责协调不同格式的输出"""
    
    def __init__(self, output_dir="./logs/thoughts"):
        self.output_dir = output_dir
        self.json_writer = JSONFileWriter(output_dir)
        self.text_writer = TextFileWriter(output_dir)
        self.terminal_logger = TerminalLogger()
        
    def write_thought(self, thought):
        """写入思考记录到所有输出目标"""
        # 写入JSON文件
        self.json_writer.append(thought)
        
        # 写入文本文件
        text_formatted = self._format_for_text(thought)
        self.text_writer.write(text_formatted)
        
        # 输出到终端（如果启用）
        if self.terminal_logger.enabled:
            self.terminal_logger.log(thought)
    
    def _format_for_text(self, thought):
        """格式化思考记录为人类可读文本"""
        # 根据thought类型格式化输出
```

### 3. 装饰器实现
```python
def record_thoughts(enabled=True):
    """记录思考过程的装饰器工厂"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 执行前记录
            if hasattr(self, '_thought_recorder') and self._thought_recorder.enabled:
                self._thought_recorder.record_call_start(func.__name__, args, kwargs)
            
            # 执行原函数
            result = func(self, *args, **kwargs)
            
            # 执行后记录
            if hasattr(self, '_thought_recorder') and self._thought_recorder.enabled:
                self._thought_recorder.record_call_end(func.__name__, result)
            
            return result
        return wrapper
    return decorator

# 应用装饰器
class MedicalAgentWithThoughts(MedicalAgent):
    """带有思考记录功能的MedicalAgent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thought_recorder = ThoughtRecorder(
            enabled=Config.ENABLE_THOUGHT_LOGGING
        )
    
    @record_thoughts()
    def run(self, user_message, patient_id=None):
        return super().run(user_message, patient_id)
```

## 数据格式

### JSON格式示例
```json
{
  "session_id": "session_20260417_094411",
  "timestamp": 1713321851.858,
  "type": "llm_call",
  "iteration": 0,
  "messages": [
    {"role": "system", "content": "你是医疗用药助手..."},
    {"role": "user", "content": "老王,30岁,60kg,轻度头疼,无过敏历史"}
  ],
  "response": {
    "content": "调用 query_drug(症状=\"头疼\")",
    "tool_calls": [
      {"name": "query_drug", "input": {"症状": "头疼"}}
    ]
  },
  "metadata": {
    "provider": "claude",
    "model": "claude-3-sonnet-20240229",
    "thinking_supported": false,
    "duration_ms": 2650,
    "estimated_tokens": 120
  }
}
```

### 文本格式示例
```
──────────────────────────────────────────────────────────────────────────────
[THINKING] Session: session_20260417_094411 | Iteration: 0 | Type: LLM Call
──────────────────────────────────────────────────────────────────────────────
Timestamp: 2026-04-17 09:44:11.858
Provider: claude | Model: claude-3-sonnet-20240229

─────────────────────────────── Messages ────────────────────────────────
System: 你是医疗用药助手，必须严格遵循以下自动工作流程...

User: 老王,30岁,60kg,轻度头疼,无过敏历史

────────────────────────────── Response ────────────────────────────────
调用 query_drug(症状="头疼")

Tool Calls:
- query_drug: {"症状": "头疼"}

────────────────────────────── Metadata ────────────────────────────────
Duration: 2.65s | Estimated Tokens: 120
Thinking Supported: No
────────────────────────────────────────────────────────────────────────
```

## 文件夹结构

```
logs/thoughts/
├── sessions/                    # 按会话组织的日志
│   ├── session_20260417_094411/
│   │   ├── thoughts.json       # 结构化JSON日志（追加模式）
│   │   ├── thoughts.log        # 人类可读文本日志
│   │   └── metadata.json       # 会话元数据
│   └── session_20260417_101522/
│       ├── thoughts.json
│       ├── thoughts.log
│       └── metadata.json
├── daily/                       # 按日期汇总的日志
│   ├── 2026-04-17.json
│   ├── 2026-04-17.log
│   └── 2026-04-16.json
└── index.json                   # 日志索引文件
```

## 配置方式

### 环境变量配置
```bash
# 启用思考记录
ENABLE_THOUGHT_LOGGING=true

# 日志级别控制
THOUGHT_LOG_LEVEL=DETAILED  # BASIC, STANDARD, DETAILED, DEBUG

# 输出目标控制
THOUGHT_LOG_TO_FILE=true
THOUGHT_LOG_TO_CONSOLE=false  # 文件日志优先
THOUGHT_LOG_DIR=./logs/thoughts

# 日志格式
THOUGHT_LOG_FORMATS=json,text  # 支持json,text两种格式

# 会话管理
THOUGHT_SESSION_AUTO_CLEANUP=true
THOUGHT_SESSION_RETENTION_DAYS=7
```

### CLI参数扩展
现有CLI接口保持不变，通过环境变量控制。可选的扩展参数：
```bash
# 现有参数保持不变
python interactive.py --verbose

# 新增思考记录相关参数（可选，不影响现有接口）
python interactive.py --with-thoughts
python interactive.py --thought-log-dir=./my_logs
```

## 集成方式

### 1. 最小化改动方案
- **不修改现有类**：创建新的装饰器类包装原有功能
- **依赖注入**：通过配置决定是否启用装饰器
- **工厂模式**：创建带思考记录的Agent实例

### 2. 装饰器应用点
```python
# 在原有代码基础上添加装饰器
from .thought_logging import with_thought_logging

# 原有创建方式保持不变
agent = MedicalAgent()

# 新的创建方式（可选）
if Config.ENABLE_THOUGHT_LOGGING:
    agent = with_thought_logging(agent)

# 或者使用工厂
from .agent_factory import create_agent
agent = create_agent(with_thoughts=Config.ENABLE_THOUGHT_LOGGING)
```

### 3. CLI集成
```python
# interactive.py中修改
def simple_interactive_mode(patient_id=None):
    # 原有代码不变...
    
    try:
        from ..core.agent import MedicalAgent
        from ..thought_logging import with_thought_logging
        
        # 创建Agent（根据配置决定是否启用思考记录）
        base_agent = MedicalAgent()
        if Config.ENABLE_THOUGHT_LOGGING:
            agent = with_thought_logging(base_agent)
        else:
            agent = base_agent
        
        # 后续代码不变...
```

## 使用说明

### 快速启用
1. 设置环境变量：
   ```bash
   export ENABLE_THOUGHT_LOGGING=true
   export THOUGHT_LOG_DIR=./logs/thoughts
   ```

2. 运行现有CLI：
   ```bash
   python interactive.py
   ```

3. 查看日志文件：
   ```bash
   ls -la ./logs/thoughts/sessions/
   tail -f ./logs/thoughts/sessions/latest/thoughts.log
   ```

### 配置文件示例
在项目根目录创建`.thought_logging.env`：
```bash
# 思考记录配置
ENABLE_THOUGHT_LOGGING=true
THOUGHT_LOG_LEVEL=DETAILED
THOUGHT_LOG_TO_FILE=true
THOUGHT_LOG_TO_CONSOLE=false
THOUGHT_LOG_DIR=./logs/thoughts
THOUGHT_LOG_FORMATS=json,text
```

### 日志文件说明
- **thoughts.json**：结构化JSON格式，便于程序分析
- **thoughts.log**：人类可读文本格式，便于人工查看
- **metadata.json**：会话元数据，包括配置、统计信息等

## 测试计划

### 单元测试
1. **ThoughtRecorder测试**：验证数据收集功能
2. **OutputManager测试**：验证多格式输出功能
3. **装饰器测试**：验证装饰器包装功能
4. **配置测试**：验证配置加载和验证

### 集成测试
1. **与Agent集成测试**：验证思考记录不影响原有功能
2. **日志文件生成测试**：验证两种格式的日志文件正确生成
3. **性能测试**：验证启用思考记录后的性能影响
4. **CLI兼容性测试**：验证现有CLI接口完全不变

### 验收标准
1. ✅ 现有CLI接口完全不变
2. ✅ 思考记录功能可通过配置开关控制
3. ✅ 生成两种格式的日志文件
4. ✅ 日志内容包含完整的思考过程
5. ✅ 性能开销在可接受范围内（<20%）
6. ✅ 错误处理完善，记录失败不影响主流程

## 实施优先级

### 第一阶段（核心功能）
1. 实现ThoughtRecorder和OutputManager
2. 实现JSON和文本文件写入器
3. 创建配置管理系统
4. 实现基础装饰器

### 第二阶段（集成优化）
1. 与MedicalAgent和LLMClient集成
2. 添加会话管理和日志轮转
3. 实现性能监控和统计
4. 添加测试覆盖率

### 第三阶段（高级功能）
1. 支持thinking参数（如果LLM API支持）
2. 添加日志分析工具
3. 实现Web日志查看界面（可选）
4. 添加告警和监控功能

---
**设计完成时间**：2026-04-17  
**设计状态**：待用户评审  
**实施预估**：2-3天开发时间