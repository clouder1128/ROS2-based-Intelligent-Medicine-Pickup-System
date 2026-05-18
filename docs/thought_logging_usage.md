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